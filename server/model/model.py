import logging
import uuid
from dataclasses import dataclass
from typing import List
from pathlib import Path

import pandas as pd
import sqlalchemy as sqla
from pyomo.core import AbstractModel
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition, SolverResults
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship, registry

import optimization.models
from model.enums import Degree, UniversityRole, SolverEnum

from model.hashable import Hashable
from model.string_enum import StringEnum

mapper_registry = registry()
metadata = mapper_registry.metadata


# The annotation is needed to avoid having to declare a boilerplate class...
# https://docs.sqlalchemy.org/en/20/orm/declarative_styles.html#declarative-mapping-using-a-decorator-no-declarative-base
@mapper_registry.mapped
@dataclass
class Student(Hashable):
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

    def __repr__(self):
        return f"Student({self.id=}, {self.matriculation_number=}, {self.name=}, {self.surname=}, " \
               f"{self.phone_number=}, {self.personal_email=}, {self.university_email=})"

    def hash(self):
        return Hashable.hash_data(repr(self))


@mapper_registry.mapped
@dataclass
class Professor(Hashable):
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

    def __repr__(self):
        return f"Professor({self.id=}, {self.name=}, {self.surname=}, {self.role=})"

    def hash(self):
        return Hashable.hash_data(repr(self))


@mapper_registry.mapped
@dataclass
class Commission(Hashable):
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
                    entry.supervisor.id,
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
                        entry.counter_supervisor.id,
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
            columns=["ID_Studente", "Cognome", "Nome", "Durata", "ID_Relatore", "Relatore", "Ruolo", "Mattina",
                     "Pomeriggio", "ID_Controrelatore", "Controrelatore", "Ruolo", "Mattina", "Pomeriggio"]
        )

        df.to_excel(xls_path, index=False)

    def __repr__(self):
        return f"Commission({self.id=}, {self.title=}, {self.entries=})"

    def hash(self):
        # Hash all the entries
        return Hashable.hash_data(repr(self) + "".join([entry.hash() for entry in self.entries]))


@mapper_registry.mapped
@dataclass
class CommissionEntry(Hashable):
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

    def __repr__(self):
        return f"CommissionEntry({self.id=}, {self.commission_id=}, {self.candidate=}, {self.degree_level=}, " \
               f"{self.supervisor=} {self.supervisor_assistant=}, {self.counter_supervisor=})"

    def hash(self):
        return Hashable.hash_data(repr(self))


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


@mapper_registry.mapped
@dataclass
class SolutionCommission:
    # Originally it was intended to have a composite primary key, but it is bringing more problems than it solves.
    # So we are going to use a single primary key and just foreign keys to the other tables.
    __tablename__ = "solution_commissions"

    id: int = Column(sqla.Integer, primary_key=True, autoincrement=True, nullable=False)

    # The specific commission number of the commission. It is just to have some sort of order, if needed.
    order: int = Column(sqla.Integer, nullable=False)

    morning: bool = Column(sqla.Boolean, nullable=False, server_default='True', default=True)

    # The commission that this solution is for
    commission_id: int = Column(sqla.Integer, ForeignKey('commissions.id'), nullable=False)
    commission: Commission = relationship("Commission")

    # The optimization configuration that generated this solution
    opt_config_id: int = Column(sqla.Integer, ForeignKey('optimization_configurations.id'), nullable=False)
    opt_config: OptimizationConfiguration = relationship("OptimizationConfiguration")

    duration: int = Column(sqla.Integer, nullable=False)

    version_hash: str = Column(sqla.String(64), nullable=False)

    _solution_commission_professors = sqla.Table(
        'solution_commission_professors', metadata,
        Column('solution_commission_id', sqla.Integer, ForeignKey('solution_commissions.id'), primary_key=True),
        Column('professor_id', sqla.Integer, ForeignKey('professors.id'), primary_key=True)
    )

    _solution_commission_students = sqla.Table(
        'solution_commission_students', metadata,
        Column('solution_commission_id', sqla.Integer, ForeignKey('solution_commissions.id'), primary_key=True),
        Column('student_id', sqla.Integer, ForeignKey('students.id'), primary_key=True)
    )

    professors: List['Professor'] = relationship("Professor", secondary=_solution_commission_professors)
    students: List['Student'] = relationship("Student", secondary=_solution_commission_students)

    __table_args__ = (
        sqla.UniqueConstraint('commission_id', 'order', 'opt_config_id'),
    )

    def __init__(self, version_hash: str):
        self.duration = 0
        self.professors = []
        self.students = []
        # The version hash is used to identify the version of the model that generated this solution
        # It is used to avoid having to recompute the solution if the model hasn't changed.
        # It should be treated as the root of a variation of a merkle tree.
        self.version_hash = version_hash

    @staticmethod
    def generate_from_model(conf: OptimizationConfiguration, model: AbstractModel, version_hash: str) -> tuple[
        List['SolutionCommission'], List['SolutionCommission']]:
        from session_maker import SessionMakerSingleton
        session: sqla.orm.Session
        with SessionMakerSingleton.get_session_maker().begin() as session:
            # noinspection PyShadowingNames
            def extract_commissions(model_commissions, offset=0, morning=True):
                from pyomo.environ import value
                commissions = []

                for commission_id, commission in enumerate(model_commissions):
                    new_commission = SolutionCommission(version_hash)
                    new_commission.morning = morning

                    for index, professor in model.docenti.iterrows():
                        if value(model.z[professor['Relatore'], commission]) > 0.8:
                            session_professor = session.query(Professor).filter_by(id=int(professor['ID'])).first()
                            new_commission.professors.append(session_professor)

                    for candidate in model.candidati:
                        if value(model.x[candidate, commission]) > 0.8:
                            session_candidate = session.query(Student).filter_by(id=int(candidate)).first()

                            new_commission.students.append(session_candidate)
                            new_commission.duration += int(model.tesisti['Durata'][candidate])

                    commissions.append(new_commission)

                # Let's filter out the commissions that aren't used
                used_commissions = [comm for comm in commissions if comm.duration > 0]

                # Now we assign the ID to the commissions
                for index, comm in enumerate(used_commissions):
                    comm.order = index + offset

                return used_commissions

            morning_commissions = extract_commissions(model.commissioni_mattina)
            afternoon_commissions = extract_commissions(model.commissioni_pomeriggio,
                                                        offset=len(morning_commissions),
                                                        morning=False)

            # Set the configuration id of each commissionsolution
            for comm in morning_commissions + afternoon_commissions:
                # We need to set via ID because the configuration object is detached from the database.
                comm.opt_config_id = conf.id
                comm.commission_id = conf.commission_id

            session.add_all(morning_commissions)
            session.add_all(afternoon_commissions)

            session.commit()

            return morning_commissions, afternoon_commissions
