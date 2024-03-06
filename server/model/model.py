import enum
import logging
import uuid
from dataclasses import dataclass
from typing import List
from pathlib import Path

import pandas as pd
import pyomo.environ
import sqlalchemy as sqla
from pyomo.core import AbstractModel
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition, SolverResults
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import Mapped, relationship, registry
from sqlalchemy.types import TypeDecorator, String

import optimization.models
from utils.logging import redirect_stdout, redirect_stderr

mapper_registry = registry()


class StringEnum(TypeDecorator):
    """
    A custom type for SQLAlchemy to store enums as strings in the database,
    while representing them as enum objects in Python.
    """
    impl = String

    def __init__(self, enum_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_type = enum_type

    def process_bind_param(self, value, dialect):
        """Convert enum object to string before storing in the database."""
        return value.value if value is not None else None

    def process_result_value(self, value, dialect):
        """Convert string back to enum object when loading from the database."""
        return self.enum_type(value) if value is not None else None


class Degree(enum.Enum):
    BACHELORS = "bachelors"
    MASTERS = "masters"


# The annotation is needed to avoid having to declare a boilerplate class...
# https://docs.sqlalchemy.org/en/20/orm/declarative_styles.html#declarative-mapping-using-a-decorator-no-declarative-base
@mapper_registry.mapped
@dataclass
class Student:
    _tablename = 'students'
    # _id_seq = sqla.Sequence(_tablename + "_id_seq")

    __table__ = sqla.Table(
        _tablename,
        mapper_registry.metadata,
        Column("id", sqla.Integer, primary_key=True, autoincrement=True, nullable=False),
        Column("matriculation_number", sqla.Integer, nullable=False),
        Column("name", sqla.String(128), nullable=False),
        Column("surname", sqla.String(128), nullable=False),
        Column("phone_number", sqla.String(32), nullable=False),
        Column("personal_email", sqla.String(256), nullable=False),
        Column("university_email", sqla.String(256), nullable=False)
    )

    id: int
    matriculation_number: int
    name: str
    surname: str
    phone_number: str
    personal_email: str
    university_email: str

    def __init__(self, matriculation_number: int, name: str, surname: str, phone_number: str, personal_email: str,
                 university_email: str):
        self.matriculation_number = matriculation_number
        self.name = name
        self.surname = surname
        self.phone_number = phone_number
        self.personal_email = personal_email
        self.university_email = university_email

    def serialize(self):
        return {
            'id': self.id,
            'matriculation_number': self.matriculation_number,
            'name': self.name,
            'surname': self.surname,
            'phone_number': self.phone_number,
            'personal_email': self.personal_email,
            'university_email': self.university_email
        }

    @property
    def full_name(self):
        return f"{self.surname} {self.name}"


class UniversityRole(enum.Enum):
    ORDINARY = "ordinary"
    ASSOCIATE = "associate"
    RESEARCHER = "researcher"
    UNSPECIFIED = "unspecified"

    @property
    def abbr(self):
        if self == UniversityRole.ORDINARY:
            return "PO"
        elif self == UniversityRole.ASSOCIATE:
            return "PA"
        elif self == UniversityRole.RESEARCHER:
            return "RIC"
        else:
            raise ValueError("Role not set.")


@mapper_registry.mapped
@dataclass
class Professor:
    __tablename__ = 'professors'

    id: int = Column(sqla.Integer, primary_key=True, autoincrement=True, nullable=False)
    name: str = Column(sqla.String(128), nullable=False)
    surname: str = Column(sqla.String(128), nullable=False)
    role: UniversityRole = Column(sqla.Enum(UniversityRole), nullable=False, default=UniversityRole.UNSPECIFIED)

    def __init__(self, name: str, surname: str, role: UniversityRole = UniversityRole.UNSPECIFIED):
        self.name = name
        self.surname = surname
        self.role = role

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'surname': self.surname,
            'role': self.role.value
        }

    @property
    def full_name(self):
        return f"{self.surname} {self.name}"


@mapper_registry.mapped
@dataclass
class Commission:
    __tablename__ = "commissions"

    id: int = Column(sqla.Integer, primary_key=True, autoincrement=True, nullable=False)
    title: str = Column(sqla.String(256), nullable=False)
    entries: List['CommissionEntry'] = relationship(
        "CommissionEntry",
        back_populates="commission",
        cascade="all, delete-orphan"
    )

    def __init__(self, title: str):
        self.title = title
        self.entries = []

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'entries': [entry.serialize() for entry in self.entries]
        }

    def export_xls(self, base_path: Path):
        xls_path = base_path / "val.xls"

        entries = []
        for entry in self.entries:
            try:
                entity = [
                    entry.candidate.id,
                    entry.candidate.surname,
                    entry.candidate.name,
                    entry.duration,
                    entry.supervisor.full_name,
                    entry.supervisor.role.abbr,
                    'SI',
                    'SI'
                ]
            except ValueError as e:
                raise ValueError(f"Professor '{entry.supervisor.full_name}' doesn't have a role") from e

            if entry.counter_supervisor is not None:
                try:
                    entity.extend([
                        entry.counter_supervisor.full_name,
                        entry.counter_supervisor.role.abbr,
                        'SI',
                        'SI'
                    ])
                except ValueError as e:
                    raise ValueError(f"Professor '{entry.counter_supervisor.full_name}' doesn't have a role") from e

            # todo do the same for the supervisor assistant

            entries.append(entity)

        df = pd.DataFrame(
            entries,
            columns=["ID", "Cognome", "Nome", "Durata", "Relatore", "Ruolo", "Mattina", "Pomeriggio", "Controrelatore",
                     "Ruolo", "Mattina", "Pomeriggio"]
        )

        df.to_excel(xls_path, index=False)


class TimeAvaliability(enum.Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    ALWAYS = "always"

    @property
    def available_morning(self):
        return self == TimeAvaliability.MORNING or self == TimeAvaliability.ALWAYS

    @property
    def available_afternoon(self):
        return self == TimeAvaliability.AFTERNOON or self == TimeAvaliability.ALWAYS


@mapper_registry.mapped
@dataclass
class CommissionEntry:
    __tablename__ = "commission_entries"

    id: int = Column(sqla.Integer, primary_key=True, autoincrement=True, nullable=False)

    commission_id = Column(sqla.Integer, ForeignKey('commissions.id'), nullable=False)
    commission: Commission = relationship("Commission", back_populates="entries")

    candidate_id: int = Column(sqla.Integer, ForeignKey('students.id'), nullable=False)
    candidate: Student = relationship(
        'Student',
        foreign_keys=[candidate_id],
        cascade="all, delete-orphan",
        single_parent=True
    )

    degree_level: Degree = Column(sqla.Enum(Degree), nullable=False)

    # Professor-Entry Relationships
    supervisor_id: int = Column(sqla.Integer, ForeignKey('professors.id'), nullable=False)
    supervisor: Professor = relationship('Professor', foreign_keys=[supervisor_id])
    # Co-relatore
    supervisor_assistant_id: int = Column(sqla.Integer, ForeignKey('professors.id'), nullable=True)
    supervisor_assistant: Professor | None = relationship('Professor', foreign_keys=[supervisor_assistant_id])

    counter_supervisor_id: int = Column(sqla.Integer, ForeignKey('professors.id'), nullable=True)
    counter_supervisor: Professor | None = relationship('Professor', foreign_keys=[counter_supervisor_id])

    def __init__(self,
                 candidate: Student,
                 degree_level: Degree,
                 supervisor: Professor,
                 supervisor_assistant: Professor = None,
                 counter_supervisor: Professor = None):
        self.candidate = candidate
        self.degree_level = degree_level
        self.supervisor = supervisor
        self.supervisor_assistant = supervisor_assistant
        self.counter_supervisor = counter_supervisor

    def serialize(self):
        return {
            'id': self.id,
            'commission_id': self.commission_id,
            'candidate': self.candidate.serialize(),
            'degree_level': self.degree_level.value,
            'supervisor': self.supervisor.serialize(),
            'supervisor_assistant': self.supervisor_assistant.serialize() if self.supervisor_assistant else None,
            'counter_supervisor': self.counter_supervisor.serialize() if self.counter_supervisor else None
        }

    @property
    def duration(self):
        return 15 if self.degree_level == Degree.BACHELORS else 20 if self.counter_supervisor is None else 30


class SolverEnum(enum.Enum):
    CPLEX = 'cplex'
    GLPK = 'glpk'
    GUROBI = 'gurobi'


class OptimizationConfiguration:
    __tablename__ = "optimization_configurations"

    id: int
    commission_id: int
    max_duration: int = 210
    max_commissions_morning: int = 6
    max_commissions_afternoon: int = 6

    online: bool = False
    min_professor_number: int | None = 3
    min_professor_number_masters: int | None = 5
    max_professor_numer: int | None = 7

    solver: SolverEnum = SolverEnum.CPLEX
    optimization_time_limit: int = 60
    optimization_gap: float = 0.005

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

    def solver_wrapper(self, cc_path: Path):
        log_path = cc_path / "log.txt"
        logger = logging.getLogger(name=str(uuid.uuid4()))
        logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        try:
            self._solve(cc_path)
        except Exception as e:
            logger.error(f"An error occurred while solving the optimization problem: {e}")
            return None

    def _solve(self, cc_path: Path):

        # excel_path = cc_path / "val.xls"
        dat_path = cc_path / "temp.dat"

        model: AbstractModel
        if self.online:
            # mindurata
            model = optimization.models.create_min_durata_model(dat_path)
        else:
            # maxdurata
            model = optimization.models.create_max_durata_model(dat_path)

        model_filename = cc_path / "model.lp"
        # Actually create the model that will be solved
        model.write(str(model_filename), io_options={'symbolic_solver_labels': True})

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

        solver = SolverFactory(self.solver.value, **solver_arguments)
        solver_log_path = cc_path / "solver.log"
        results: SolverResults = solver.solve(model, tee=True, keepfiles=True, logfile=str(solver_log_path.absolute()))

        is_solver_ok = results.solver.status == SolverStatus.ok
        solver_reachec_optimality = results.solver.termination_condition == TerminationCondition.optimal
        solver_reached_time_limit = results.solver.termination_condition == TerminationCondition.maxTimeLimit

        if is_solver_ok and (solver_reachec_optimality or solver_reached_time_limit):
            return SolutionHandler.extract_solution(self, model, results)


class Solution:
    pass


class SolutionHandler:
    sol = None

    # id commission
    # id configuration

    def __init__(self, sol):
        self.sol = sol

    @staticmethod
    def extract_solution(conf: OptimizationConfiguration, model: AbstractModel, result: SolverResults) -> Solution:
        s = Solution()
        print(repr(conf))
        print(repr(model))
        print(repr(result))

        def output_commissione(model: AbstractModel, commission: pyomo.environ.Set):
            from pyomo.core.expr import evaluate_expression
            from pyomo.environ import value
            model.model_name = "maxDurata"

            out_str = ""
            for c in commission:
                out_str += f'y[{c}] = {model.y[c]}\n'
                out_str += 'durComm = {}\n'.format(value(sum(model.durata[cand] * model.x[cand, c] for cand in model.candidati)))

                # if model.y[c] > 0.8:
                #     mag = 'MAG' if model.model_name == 'minDurata' and model.y2[c] else ''
                out_str += 'Commissione {} {}\n'.format(c, "")
                out_str += 'Docenti:\n'
                for d in model.nomi_docenti:
                    if value(model.z[d, c]) > 0.8:
                        out_str += '{}\n'.format(d)  # model.z[d,c])
                out_str += '\nTesisti:\n'
                durata = 0
                for t in model.candidati:
                    if value(model.x[t, c]) > 0.8:
                        tMag = '*' if model.tesisti['Durata'][t] > 15 else ''
                        out_str += '{} {} {}\n'.format(model.tesisti['Cognome'][t], model.tesisti['Nome'][t],
                                                         tMag)  # ,model.x[t,c])
                        durata += model.tesisti['Durata'][t]
                out_str += 'Durata commissione: {} min\n\n'.format(durata)
            return out_str

        print(output_commissione(model, model.commissioni_mattina))
        print(output_commissione(model, model.commissioni_pomeriggio))

        return s
