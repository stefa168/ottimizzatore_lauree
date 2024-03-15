from dataclasses import dataclass
from typing import List

import sqlalchemy as sqla
from pyomo.core import AbstractModel
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship, registry

from model.commission import Commission
from model.optimization_configuration import OptimizationConfiguration
from model.professor import Professor
from model.student import Student

mapper_registry = registry()
metadata = mapper_registry.metadata


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
