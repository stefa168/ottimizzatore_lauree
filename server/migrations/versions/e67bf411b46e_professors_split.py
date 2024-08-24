"""Professors Split

Revision ID: e67bf411b46e
Revises: a55ee52d742e
Create Date: 2024-08-24 16:47:30.979176

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e67bf411b46e'
down_revision: Union[str, None] = 'a55ee52d742e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # https://stackoverflow.com/questions/14845203/altering-an-enum-field-using-alembic
    op.execute('alter type time_availability add value \'SPLIT\' after \'ALWAYS\'')


def downgrade() -> None:
    raise NotImplementedError("Downgrade from this version is not possible.")
