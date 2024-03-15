import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

import sqlalchemy as sqla
from pyomo.core import AbstractModel
from pyomo.opt import SolverFactory, SolverResults, SolverStatus, TerminationCondition
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship, registry

import optimization.models
from model.commission import Commission
from model.enums import SolverEnum
from model.hashable import Hashable
from model.solution_commission import SolutionCommission
from model.string_enum import StringEnum

mapper_registry = registry()
metadata = mapper_registry.metadata


@mapper_registry.mapped
@dataclass
class OptimizationConfiguration(Hashable):
    __tablename__ = "optimization_configurations"

    id: int = Column(sqla.Integer, primary_key=True, autoincrement=True, nullable=False)

    commission_id: int = Column(sqla.Integer, ForeignKey('commissions.id'), nullable=False)
    commission: Commission = relationship("Commission")

    max_duration: int = Column(sqla.Integer, nullable=False, server_default='210', default=210)
    max_commissions_morning: int = Column(sqla.Integer, nullable=False, server_default='6', default=6)
    max_commissions_afternoon: int = Column(sqla.Integer, nullable=False, server_default='6', default=6)

    online: bool = Column(sqla.Boolean, nullable=False, server_default='False', default=False)
    min_professor_number: int | None = Column(sqla.Integer, nullable=True)
    min_professor_number_masters: int | None = Column(sqla.Integer, nullable=True)
    max_professor_numer: int | None = Column(sqla.Integer, nullable=True)

    solver: SolverEnum = Column(StringEnum(SolverEnum), nullable=False, default=SolverEnum.CPLEX,
                                server_default=SolverEnum.CPLEX.value)
    optimization_time_limit: int = Column(sqla.Integer, nullable=False, server_default='60', default=60)
    optimization_gap: float = Column(sqla.Float, nullable=False, server_default='0.005', default=0.005)

    def __init__(self, config_id: int, commission_id: int):
        self.id = config_id
        self.commission_id = commission_id

    def create_dat_file(self, base_path: Path) -> (Path, Path):
        dat_file = base_path / "temp.dat"
        excel_path = base_path / "val.xls"

        base_path.mkdir(parents=True, exist_ok=True)

        morning_commissions = list(range(0, self.max_commissions_morning))
        afternoon_commissions = list(range(
            self.max_commissions_morning,
            self.max_commissions_morning + self.max_commissions_afternoon
        ))

        with open(dat_file, "w") as f:
            f.write(f"param max_durata := {self.max_duration};\n")
            f.write(f"set commissioni_mattina := {' '.join(map(str, morning_commissions))};\n")
            f.write(f"set commissioni_pomeriggio := {' '.join(map(str, afternoon_commissions))};\n")
            f.write(f"param excel_path := \"{excel_path.resolve()}\";\n")

            if self.online:
                f.write(f"param minDocenti := {self.min_professor_number};\n")
                f.write(f"param minDocentiMag := {self.min_professor_number_masters};\n")
                f.write(f"param max_doc := {self.max_professor_numer};\n")

        return base_path, dat_file

    def __repr__(self):
        return f"OptimizationConfiguration({self.id=}, {self.commission_id=}, {self.max_duration=}, " \
               f"{self.max_commissions_morning=}, {self.max_commissions_afternoon=}, {self.online=}, " \
               f"{self.min_professor_number=}, {self.min_professor_number_masters=}, {self.max_professor_numer=}, " \
               f"{self.solver=}, {self.optimization_time_limit=}, {self.optimization_gap=})"

    def solver_wrapper(self, cc_path: Path, version_hash: str):
        log_path = cc_path / "log.txt"
        logger = logging.getLogger(name=str(uuid.uuid4()))
        logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        logger.info(f"Starting optimization for commission with ID ${self.commission_id},"
                    f" version hash ${version_hash}.")

        try:
            self._solve(cc_path, logger, version_hash)
        except Exception as e:
            logger.error(f"An error occurred while solving the optimization problem: {e}")
            return None
        else:
            logger.info("Optimization completed and correctly saved to database.")

    def _solve(self, cc_path: Path, logger: logging.Logger, version_hash: str):

        # excel_path = cc_path / "val.xls"
        dat_path = cc_path / "temp.dat"

        model: AbstractModel
        if self.online:
            # mindurata
            model = optimization.models.create_min_durata_model(dat_path)
        else:
            # maxdurata
            model = optimization.models.create_max_durata_model(dat_path)
        logger.debug("Optimization model created")

        model_filename = cc_path / "model.lp"
        # Actually create the model that will be solved
        model.write(str(model_filename), io_options={'symbolic_solver_labels': True})
        logger.debug(f"Model written to file ${model_filename}")

        solver_arguments = dict()
        solver_arguments['options'] = dict()

        if self.solver == SolverEnum.CPLEX:
            solver_arguments['options']['timelimit'] = self.optimization_time_limit
            solver_arguments['options']['mip_tolerances_mipgap'] = self.optimization_gap
            solver_arguments['executable'] = "/opt/ibm/ILOG/CPLEX_Studio128/cplex/bin/x86-64_linux/cplex"
        elif self.solver == SolverEnum.GLPK:
            solver_arguments['options']['tmlim'] = self.optimization_time_limit
            solver_arguments['options']['mipgap'] = self.optimization_gap
        elif self.solver == SolverEnum.GUROBI:
            solver_arguments['options']['TimeLimit'] = self.optimization_time_limit
            solver_arguments['options']['MIPGap'] = self.optimization_gap
        else:
            raise ValueError("Unknown solver")

        logger.debug("Options for selected solver set")

        solver = SolverFactory(self.solver.value, **solver_arguments)
        solver_log_path = cc_path / "solver.log"
        logger.info("Starting solver...")
        results: SolverResults = solver.solve(model, tee=True, keepfiles=True, logfile=str(solver_log_path.absolute()))
        logger.info("The solver has exited.")

        is_solver_ok = results.solver.status == SolverStatus.ok
        solver_reachec_optimality = results.solver.termination_condition == TerminationCondition.optimal
        solver_reached_time_limit = results.solver.termination_condition == TerminationCondition.maxTimeLimit

        logger.debug(f"Solver status: {results.solver.status}")

        if is_solver_ok and (solver_reachec_optimality or solver_reached_time_limit):
            return SolutionCommission.generate_from_model(self, model, version_hash)

    def hash(self):
        return Hashable.hash_data(repr(self))
