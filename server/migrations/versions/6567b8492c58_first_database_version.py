"""First database version

Revision ID: 6567b8492c58
Revises: 
Create Date: 2024-05-22 20:15:26.305713

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from model import StringEnum, SolverEnum

# revision identifiers, used by Alembic.
revision: str = '6567b8492c58'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('commissions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('title', sa.String(length=256), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('professors',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('surname', sa.String(length=128), nullable=False),
    sa.Column('role', sa.Enum('ORDINARY', 'ASSOCIATE', 'RESEARCHER', 'UNSPECIFIED', name='universityrole'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('students',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('matriculation_number', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('surname', sa.String(length=128), nullable=False),
    sa.Column('phone_number', sa.String(length=32), nullable=False),
    sa.Column('personal_email', sa.String(length=256), nullable=False),
    sa.Column('university_email', sa.String(length=256), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('commission_entries',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('commission_id', sa.Integer(), nullable=False),
    sa.Column('candidate_id', sa.Integer(), nullable=False),
    sa.Column('degree_level', sa.Enum('BACHELORS', 'MASTERS', name='degree'), nullable=False),
    sa.Column('supervisor_id', sa.Integer(), nullable=False),
    sa.Column('supervisor_assistant_id', sa.Integer(), nullable=True),
    sa.Column('counter_supervisor_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['candidate_id'], ['students.id'], ),
    sa.ForeignKeyConstraint(['commission_id'], ['commissions.id'], ),
    sa.ForeignKeyConstraint(['counter_supervisor_id'], ['professors.id'], ),
    sa.ForeignKeyConstraint(['supervisor_assistant_id'], ['professors.id'], ),
    sa.ForeignKeyConstraint(['supervisor_id'], ['professors.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('optimization_configurations',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('title', sa.String(length=256), server_default='Nuova configurazione', nullable=False),
    sa.Column('commission_id', sa.Integer(), nullable=False),
    sa.Column('max_duration', sa.Integer(), server_default='210', nullable=False),
    sa.Column('max_commissions_morning', sa.Integer(), server_default='6', nullable=False),
    sa.Column('max_commissions_afternoon', sa.Integer(), server_default='6', nullable=False),
    sa.Column('online', sa.Boolean(), server_default='False', nullable=False),
    sa.Column('min_professor_number', sa.Integer(), nullable=True),
    sa.Column('min_professor_number_masters', sa.Integer(), nullable=True),
    sa.Column('max_professor_numer', sa.Integer(), nullable=True),
    sa.Column('solver', StringEnum(SolverEnum), server_default='cplex', nullable=False),
    sa.Column('optimization_time_limit', sa.Integer(), server_default='60', nullable=False),
    sa.Column('optimization_gap', sa.Float(), server_default='0.005', nullable=False),
    sa.Column('run_lock', sa.Boolean(), server_default='False', nullable=False),
    sa.ForeignKeyConstraint(['commission_id'], ['commissions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('execution_details',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('commission_id', sa.Integer(), nullable=False),
    sa.Column('opt_config_id', sa.Integer(), nullable=False),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('success', sa.Boolean(), server_default='False', nullable=False),
    sa.Column('solver_reached_optimality', sa.Boolean(), server_default='False', nullable=False),
    sa.Column('solver_time_limit_reached', sa.Boolean(), server_default='False', nullable=False),
    sa.Column('error_message', sa.String(length=256), nullable=True),
    sa.Column('optimizer_log', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['commission_id'], ['commissions.id'], ),
    sa.ForeignKeyConstraint(['opt_config_id'], ['optimization_configurations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('solution_commissions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('morning', sa.Boolean(), server_default='True', nullable=False),
    sa.Column('commission_id', sa.Integer(), nullable=False),
    sa.Column('opt_config_id', sa.Integer(), nullable=False),
    sa.Column('duration', sa.Integer(), nullable=False),
    sa.Column('version_hash', sa.String(length=64), nullable=False),
    sa.ForeignKeyConstraint(['commission_id'], ['commissions.id'], ),
    sa.ForeignKeyConstraint(['opt_config_id'], ['optimization_configurations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('commission_id', 'order', 'opt_config_id')
    )
    op.create_table('solution_commission_professors',
    sa.Column('solution_commission_id', sa.Integer(), nullable=False),
    sa.Column('professor_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['professor_id'], ['professors.id'], ),
    sa.ForeignKeyConstraint(['solution_commission_id'], ['solution_commissions.id'], ),
    sa.PrimaryKeyConstraint('solution_commission_id', 'professor_id')
    )
    op.create_table('solution_commission_students',
    sa.Column('solution_commission_id', sa.Integer(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['solution_commission_id'], ['solution_commissions.id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
    sa.PrimaryKeyConstraint('solution_commission_id', 'student_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('solution_commission_students')
    op.drop_table('solution_commission_professors')
    op.drop_table('solution_commissions')
    op.drop_table('execution_details')
    op.drop_table('optimization_configurations')
    op.drop_table('commission_entries')
    op.drop_table('students')
    op.drop_table('professors')
    op.drop_table('commissions')
    # ### end Alembic commands ###
