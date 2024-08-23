"""Professors time availability

Revision ID: a55ee52d742e
Revises: 6567b8492c58
Create Date: 2024-08-23 17:50:51.641230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a55ee52d742e'
down_revision: Union[str, None] = '6567b8492c58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

time_availability_enum = sa.Enum('MORNING', 'AFTERNOON', 'ALWAYS', name='time_availability')


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    time_availability_enum.create(op.get_bind())
    op.add_column('professors', sa.Column('availability', time_availability_enum, nullable=False, server_default="ALWAYS"))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('professors', 'availability')
    time_availability_enum.drop(op.get_bind())
    # ### end Alembic commands ###
