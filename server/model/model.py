import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List
from pathlib import Path
from zoneinfo import available_timezones

import pandas as pd
import sqlalchemy as sa
from pyomo.core import AbstractModel
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition, SolverResults
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship, registry, declarative_base, Mapped, mapped_column
from watchdog.observers import Observer

import optimization.models
from model import Degree, UniversityRole, SolverEnum, Hashable, StringEnum, TimeAvailability
from session_maker import SessionMakerSingleton

from utils import FileChangeHandler

# mapper_registry = registry()
# metadata = mapper_registry.metadata

Base = declarative_base()


# The annotation is needed to avoid having to declare a boilerplate class...
# https://docs.sqlalchemy.org/en/20/orm/declarative_styles.html#declarative-mapping-using-a-decorator-no-declarative-base
@dataclass
class Student(Base, Hashable):
    __tablename__ = 'students'

    id = mapped_column(sa.Integer, primary_key=True, autoincrement=True, nullable=False)
    matriculation_number = mapped_column(sa.Integer, nullable=False)
    name = mapped_column(sa.String(128), nullable=False)
    surname = mapped_column(sa.String(128), nullable=False)
    phone_number = mapped_column(sa.String(32), nullable=False)
    personal_email = mapped_column(sa.String(256), nullable=False)
    university_email = mapped_column(sa.String(256), nullable=False)

    def __init__(self, matriculation_number: int, name: str, surname: str, phone_number: str, personal_email: str,
                 university_email: str):
        super().__init__()
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


@dataclass
class Professor(Base, Hashable):
    __tablename__ = 'professors'

    id = mapped_column(sa.Integer, primary_key=True, autoincrement=True, nullable=False)
    name = mapped_column(sa.String(128), nullable=False)
    surname = mapped_column(sa.String(128), nullable=False)
    role: Mapped[UniversityRole] = mapped_column(sa.Enum(UniversityRole), nullable=False,
                                                 default=UniversityRole.UNSPECIFIED)
    availability: Mapped[TimeAvailability] = mapped_column(sa.Enum(TimeAvailability), nullable=False,
                                                           default=TimeAvailability.ALWAYS)

    def __init__(self, name: str, surname: str, role: UniversityRole = UniversityRole.UNSPECIFIED,
                 availability=TimeAvailability.ALWAYS):
        super().__init__()
        self.name = name
        self.surname = surname
        self.role = role
        self.availability = availability

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'surname': self.surname,
            'role': self.role.value,
            'availability': self.availability.value
        }

    @property
    def full_name(self):
        return f"{self.surname} {self.name}"

    def __repr__(self):
        return f"Professor({self.id=}, {self.name=}, {self.surname=}, {self.role=})"

    def hash(self):
        return Hashable.hash_data(repr(self))


@dataclass
class Commission(Base, Hashable):
    __tablename__ = "commissions"

    id = mapped_column(sa.Integer, primary_key=True, autoincrement=True, nullable=False)
    title = mapped_column(sa.String(256), nullable=False)
    entries: Mapped[List['CommissionEntry']] = relationship(
        "CommissionEntry",
        back_populates="commission",
        cascade="all, delete-orphan"
    )
    optimization_configurations: Mapped[List['OptimizationConfiguration']] = relationship(
        "OptimizationConfiguration",
        back_populates="commission",
        cascade="all, delete-orphan"
    )

    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self.entries = []

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'entries': [entry.serialize() for entry in self.entries],
            'optimization_configurations': [conf.serialize() for conf in self.optimization_configurations]
        }

    def export_xls(self, base_path: Path):
        xls_path = base_path / "val.xls"

        def si_no(yes: bool) -> str:
            return 'SI' if yes else 'NO'

        # There is a specific possibility that has been intentionally omitted:
        # It might happen that we have a professor that has to be split, however he/she also is a counter-supervisor.
        # This could cause the problem to be unsolvable.
        # A better solution has to be discussed.
        students_by_professor: dict[Professor, list[CommissionEntry]] = {}
        for entry in self.entries:
            p = entry.supervisor
            if p not in students_by_professor:
                students_by_professor[p] = []

            students_by_professor[p].append(entry)

        entries = []

        for p in students_by_professor:
            pe = students_by_professor[p]
            should_split = p.availability == TimeAvailability.SPLIT

            for index, entry, in enumerate(pe):
                morning_supervisor_availability: bool
                afternoon_supervisor_availability: bool

                supervisor = entry.supervisor

                if should_split:
                    if index <= (len(pe) / 2):
                        morning_supervisor_availability = True
                        afternoon_supervisor_availability = False
                    else:
                        morning_supervisor_availability = False
                        afternoon_supervisor_availability = True
                else:
                    morning_supervisor_availability = supervisor.availability.available_morning
                    afternoon_supervisor_availability = supervisor.availability.available_afternoon

                try:
                    supervisor = entry.supervisor
                    entity = [
                        entry.candidate.id,
                        entry.candidate.surname,
                        entry.candidate.name,
                        entry.duration,
                        supervisor.id,
                        supervisor.full_name,
                        supervisor.role.abbr,
                        si_no(morning_supervisor_availability),  # mattina
                        si_no(afternoon_supervisor_availability)  # pomeriggio
                    ]
                except ValueError as e:
                    raise ValueError(f"Professor '{entry.supervisor.full_name}' doesn't have a role") from e

                if entry.counter_supervisor is not None:
                    cs = entry.counter_supervisor
                    try:
                        entity.extend([
                            cs.id,
                            cs.full_name,
                            cs.role.abbr,
                            si_no(cs.availability.available_morning),  # mattina
                            si_no(cs.availability.available_afternoon)  # pomeriggio
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


@dataclass
class CommissionEntry(Base, Hashable):
    __tablename__ = "commission_entries"

    id = mapped_column(sa.Integer, primary_key=True, autoincrement=True, nullable=False)

    commission_id = mapped_column(sa.Integer, ForeignKey('commissions.id'), nullable=False)
    commission: Mapped[Commission] = relationship("Commission", back_populates="entries")

    candidate_id = mapped_column(sa.Integer, ForeignKey('students.id'), nullable=False)
    candidate: Mapped[Student] = relationship(
        'Student',
        foreign_keys=[candidate_id],
        cascade="all, delete-orphan",
        single_parent=True
    )

    degree_level: Mapped[Degree] = mapped_column(sa.Enum(Degree), nullable=False)

    # Professor-Entry Relationships
    supervisor_id = mapped_column(sa.Integer, ForeignKey('professors.id'), nullable=False)
    supervisor: Mapped[Professor] = relationship('Professor', foreign_keys=[supervisor_id])
    # Co-relatore
    supervisor_assistant_id = mapped_column(sa.Integer, ForeignKey('professors.id'), nullable=True)
    supervisor_assistant: Mapped[Professor | None] = relationship('Professor', foreign_keys=[supervisor_assistant_id])

    counter_supervisor_id = mapped_column(sa.Integer, ForeignKey('professors.id'), nullable=True)
    counter_supervisor: Mapped[Professor | None] = relationship('Professor', foreign_keys=[counter_supervisor_id])

    def __init__(self,
                 candidate: Student,
                 degree_level: Degree,
                 supervisor: Professor,
                 supervisor_assistant: Professor = None,
                 counter_supervisor: Professor = None):
        super().__init__()
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


@dataclass
class OptimizationConfiguration(Base, Hashable):
    __tablename__ = "optimization_configurations"

    id = mapped_column(sa.Integer, primary_key=True, autoincrement=True, nullable=False)
    title = mapped_column(sa.String(256),
                          nullable=False,
                          server_default="Nuova configurazione",
                          default="Nuova configurazione")

    commission_id = mapped_column(sa.Integer, ForeignKey('commissions.id'), nullable=False)
    commission: Mapped[Commission] = relationship("Commission")

    max_duration = mapped_column(sa.Integer, nullable=False, server_default='210', default=210)
    max_commissions_morning = mapped_column(sa.Integer, nullable=False, server_default='6', default=6)
    max_commissions_afternoon = mapped_column(sa.Integer, nullable=False, server_default='6', default=6)

    online = mapped_column(sa.Boolean, nullable=False, server_default='True', default=True)
    min_professor_number: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    min_professor_number_masters: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    max_professor_numer: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

    solver: Mapped[SolverEnum] = mapped_column(StringEnum(SolverEnum), nullable=False, default=SolverEnum.CPLEX,
                                               server_default=SolverEnum.CPLEX.value)
    optimization_time_limit = mapped_column(sa.Integer, nullable=False, server_default='60', default=60)
    optimization_gap = mapped_column(sa.Float, nullable=False, server_default='0.005', default=0.005)

    run_lock = mapped_column(sa.Boolean, nullable=False, server_default='False', default=False)

    execution_details: Mapped[List['ExecutionDetails']] = relationship(
        "ExecutionDetails",
        back_populates="opt_config",
        cascade="all, delete-orphan"
    )

    solution_commissions: Mapped[List['SolutionCommission']] = relationship(
        "SolutionCommission",
        back_populates="opt_config",
        cascade="all, delete-orphan"
    )

    def __init__(self, commission_id: int, title: str):
        super().__init__()
        self.commission_id = commission_id
        self.title = title

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

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'commission_id': self.commission_id,
            'max_duration': self.max_duration,
            'max_commissions_morning': self.max_commissions_morning,
            'max_commissions_afternoon': self.max_commissions_afternoon,
            'online': self.online,
            'min_professor_number': self.min_professor_number,
            'min_professor_number_masters': self.min_professor_number_masters,
            'max_professor_number': self.max_professor_numer,
            'solver': self.solver.value,
            'optimization_time_limit': self.optimization_time_limit,
            'optimization_gap': self.optimization_gap,
            'run_lock': self.run_lock,
            'solution_commissions': [sol.serialize() for sol in self.solution_commissions],
            'execution_details': [ed.serialize() for ed in self.execution_details]
        }

    def solver_wrapper(self, cc_path: Path, version_hash: str, logger: logging.Logger):
        logger.setLevel(logging.INFO)

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

        # Wipe the file clean if it already exists, otherwise the existing content will mess with the watchdog logger.
        solver_log_path.open("w").close()
        solver_log_handler = FileChangeHandler(logger.getChild("solver"), solver_log_path)

        # Small logger just to print the solver output to the main logger
        def solver_log_observer(new_lines):
            for line in new_lines:
                logger.debug(line)

        solver_log_handler.register_observer(solver_log_observer)

        observer = Observer()
        observer.schedule(solver_log_handler, str(solver_log_path.parent), recursive=False)
        observer.start()
        logger.info("Running solver...")
        ed = ExecutionDetails(self.commission_id, self.id)
        results: SolverResults = solver.solve(
            model,
            tee=True,
            keepfiles=True,
            logfile=str(solver_log_path.absolute())
        )
        logger.info("The solver has exited.")
        logger.debug("Stopping observer...")
        observer.stop()
        logger.debug("Observer stopped. Joining observer thread...")
        observer.join()
        logger.debug("Observer thread joined.")

        is_solver_ok = results.solver.status == SolverStatus.ok
        solver_reached_optimality = results.solver.termination_condition == TerminationCondition.optimal
        solver_reached_time_limit = results.solver.termination_condition == TerminationCondition.maxTimeLimit

        logger.debug(f"Solver status: {results.solver.status}")

        ed.finished(is_solver_ok, solver_reached_optimality, solver_reached_time_limit)
        ed.optimizer_log = solver_log_handler.read_file()

        session: sa.orm.Session
        with SessionMakerSingleton.get_session_maker().begin() as session:
            session.add(ed)
            session.commit()

        if is_solver_ok:
            if solver_reached_optimality or solver_reached_time_limit:
                # todo return also the reason why the solver stopped
                return SolutionCommission.generate_from_model(self, model, version_hash)
            else:
                # todo decide what to do in case of failure
                logger.error(f"Solver failed to reach optimality. Solver status: {results.solver.status}")
                return None
        else:
            # todo decide what to do in case of failure
            logger.error(f"Solver encountered an error. Solver status: {results.solver.status}")
            return None

    def hash(self):
        return Hashable.hash_data(repr(self))


@dataclass
class SolutionCommission(Base):
    # Originally it was intended to have a composite primary key, but it is bringing more problems than it solves.
    # So we are going to use a single primary key and just foreign keys to the other tables.
    __tablename__ = "solution_commissions"

    id = mapped_column(sa.Integer, primary_key=True, autoincrement=True, nullable=False)

    # The specific commission number of the commission. It is just to have some sort of order, if needed.
    order = mapped_column(sa.Integer, nullable=False)

    morning = mapped_column(sa.Boolean, nullable=False, server_default='True', default=True)

    # The commission that this solution is for
    commission_id = mapped_column(sa.Integer, ForeignKey('commissions.id'), nullable=False)
    commission: Mapped[Commission] = relationship("Commission")

    # The optimization configuration that generated this solution
    opt_config_id = mapped_column(sa.Integer, ForeignKey('optimization_configurations.id'), nullable=False)
    opt_config: Mapped[OptimizationConfiguration] = relationship("OptimizationConfiguration")

    duration = mapped_column(sa.Integer, nullable=False)

    version_hash = mapped_column(sa.String(64), nullable=False)

    # _solution_commission_professors = sa.Table(
    #     'solution_commission_professors', metadata,
    #     Column('solution_commission_id', sa.Integer, ForeignKey('solution_commissions.id'), primary_key=True),
    #     Column('professor_id', sa.Integer, ForeignKey('professors.id'), primary_key=True)
    # )
    #
    # _solution_commission_students = sa.Table(
    #     'solution_commission_students', metadata,
    #     Column('solution_commission_id', sa.Integer, ForeignKey('solution_commissions.id'), primary_key=True),
    #     Column('student_id', sa.Integer, ForeignKey('students.id'), primary_key=True)
    # )

    professors: Mapped[List['Professor']] = relationship("Professor", secondary="solution_commission_professors")
    students: Mapped[List['Student']] = relationship("Student", secondary="solution_commission_students")

    __table_args__ = (
        sa.UniqueConstraint('commission_id', 'order', 'opt_config_id'),
    )

    def __init__(self, version_hash: str):
        super().__init__()
        self.duration = 0
        self.professors = []
        self.students = []
        # The version hash is used to identify the version of the model that generated this solution
        # It is used to avoid having to recompute the solution if the model hasn't changed.
        # It should be treated as the root of a variation of a merkle tree.
        self.version_hash = version_hash

    @staticmethod
    def generate_from_model(conf: OptimizationConfiguration, model: AbstractModel, version_hash: str) \
            -> tuple[List['SolutionCommission'], List['SolutionCommission']]:
        from session_maker import SessionMakerSingleton
        session: sa.orm.Session
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

    def serialize(self):
        return {
            'id': self.id,
            'order': self.order,
            'morning': self.morning,
            'commission_id': self.commission_id,
            'opt_config_id': self.opt_config_id,
            'duration': self.duration,
            'version_hash': self.version_hash,
            'professors': [prof.serialize() for prof in self.professors],
            'students': [stud.serialize() for stud in self.students]
        }


class SolutionCommissionProfessor(Base):
    __tablename__ = 'solution_commission_professors'
    solution_commission_id = mapped_column(sa.Integer, ForeignKey('solution_commissions.id'), primary_key=True)
    professor_id = mapped_column(sa.Integer, ForeignKey('professors.id'), primary_key=True)


class SolutionCommissionStudent(Base):
    __tablename__ = 'solution_commission_students'
    solution_commission_id = mapped_column(sa.Integer, ForeignKey('solution_commissions.id'), primary_key=True)
    student_id = mapped_column(sa.Integer, ForeignKey('students.id'), primary_key=True)


@dataclass
class ExecutionDetails(Base, Hashable):
    __tablename__ = "execution_details"

    # We are using a separate ID because we want to keep track of the execution details even if the optimization
    # configuration is run again with the override.
    id = mapped_column(sa.Integer, primary_key=True, autoincrement=True, nullable=False)

    # todo remove this foreign key
    commission_id = mapped_column(sa.Integer, ForeignKey('commissions.id'), nullable=False)
    commission: Mapped[Commission] = relationship("Commission")

    opt_config_id = mapped_column(sa.Integer, ForeignKey('optimization_configurations.id'), nullable=False)
    opt_config: Mapped[OptimizationConfiguration] = relationship("OptimizationConfiguration")

    start_time = mapped_column(sa.DateTime(timezone=True), nullable=False)
    end_time = mapped_column(sa.DateTime(timezone=True), nullable=True)

    success = mapped_column(sa.Boolean, nullable=False, server_default='False', default=False)
    solver_reached_optimality = mapped_column(sa.Boolean, nullable=False, server_default='False', default=False)
    solver_time_limit_reached = mapped_column(sa.Boolean, nullable=False, server_default='False', default=False)
    error_message = mapped_column(sa.String(256), nullable=True)
    optimizer_log = mapped_column(sa.Text, nullable=True)

    def __init__(self, commission_id: int, opt_config_id: int, start_time: datetime = datetime.now()):
        super().__init__()
        self.commission_id = commission_id
        self.opt_config_id = opt_config_id
        self.start_time = start_time

    def serialize(self):
        return {
            'id': self.id,
            'commission_id': self.commission_id,
            'opt_config_id': self.opt_config_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'success': self.success,
            'solver_reached_optimality': self.solver_reached_optimality,
            'solver_time_limit_reached': self.solver_time_limit_reached,
            'error_message': self.error_message,
            'optimizer_log': self.optimizer_log
        }

    def __repr__(self):
        return f"ExecutionDetails({self.id=}, {self.commission_id=}, {self.opt_config_id=}, {self.start_time=}, " \
               f"{self.end_time=}, {self.success=}, {self.error_message=})"

    def hash(self):
        return Hashable.hash_data(repr(self))

    def finished(self, ok, optimality_reached, time_limit_reached):
        self.end_time = datetime.now()
        self.success = ok
        self.solver_reached_optimality = optimality_reached
        self.solver_time_limit_reached = time_limit_reached
