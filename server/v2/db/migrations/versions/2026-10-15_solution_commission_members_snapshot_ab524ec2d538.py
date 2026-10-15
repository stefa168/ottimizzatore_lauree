"""solution commission members snapshot

Revision ID: ab524ec2d538
Revises: 4eec6e13b236
Create Date: 2026-10-15 21:59:24.017957

"""

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from advanced_alchemy.types import EncryptedString, EncryptedText, GUID, ORA_JSONB, DateTimeUTC, StoredObject, PasswordHash
from sqlalchemy import Text  # noqa: F401
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades", "data_upgrades", "data_downgrades"]

sa.GUID = GUID
sa.DateTimeUTC = DateTimeUTC
sa.ORA_JSONB = ORA_JSONB
sa.EncryptedString = EncryptedString
sa.EncryptedText = EncryptedText
sa.StoredObject = StoredObject

# revision identifiers, used by Alembic.
revision = 'ab524ec2d538'
down_revision = '4eec6e13b236'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            schema_upgrades()
            data_upgrades()

def downgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            data_downgrades()
            schema_downgrades()

# Solved commissions keep a snapshot of their members (the person, and how they sat: split part, substitute of whom),
# instead of depending on the session professors, which are deleted when splits or substitutes change.
TABLE = 'solution_commission_professors'

relation_enum = postgresql.ENUM('ORIGINAL', 'SPLIT', 'SUBSTITUTE', name='session_professor_relation_enum',
                                create_type=False)
availability_enum = postgresql.ENUM('MORNING', 'AFTERNOON', 'ALWAYS', name='time_availability_enum',
                                    create_type=False)


def schema_upgrades() -> None:
    """schema upgrade migrations go here."""
    op.drop_constraint('fk_solution_commission_professors_professor_id_session__4b4e', TABLE, type_='foreignkey')
    op.drop_constraint('fk_solution_commission_professors_solution_commission_i_9d51', TABLE, type_='foreignkey')
    op.drop_constraint('pk_solution_commission_professors', TABLE, type_='primary')

    # The old column referenced the session professor
    op.alter_column(TABLE, 'professor_id', new_column_name='session_professor_id', nullable=True)
    op.add_column(TABLE, sa.Column('professor_id', sa.Integer(), nullable=True))
    op.add_column(TABLE, sa.Column('relation', relation_enum, nullable=False, server_default='ORIGINAL'))
    op.add_column(TABLE, sa.Column('part', sa.Integer(), nullable=True))
    op.add_column(TABLE, sa.Column('substitute_of_id', sa.Integer(), nullable=True))
    op.add_column(TABLE, sa.Column('availability', availability_enum, nullable=False, server_default='ALWAYS'))

    # Backfill from the session professors
    op.execute(f"""
        UPDATE {TABLE} AS m
        SET professor_id = sp.professor_id, relation = sp.relation, availability = sp.availability
        FROM session_professors AS sp
        WHERE sp.id = m.session_professor_id
    """)
    # Split parts are numbered in creation order, like the professors page does
    split_parts = """
        SELECT id, row_number() OVER (PARTITION BY derived_from_id ORDER BY id) AS part
        FROM session_professors WHERE relation = 'SPLIT'
    """
    op.execute(f"""
        UPDATE {TABLE} AS m SET part = s.part
        FROM ({split_parts}) AS s
        WHERE s.id = m.session_professor_id
    """)
    op.execute(f"""
        UPDATE {TABLE} AS m SET part = s.part
        FROM session_professors AS sub JOIN ({split_parts}) AS s ON s.id = sub.derived_from_id
        WHERE sub.id = m.session_professor_id AND sub.relation = 'SUBSTITUTE'
    """)
    # A substitute replaces the original professor (directly, or one of their split parts)
    op.execute(f"""
        UPDATE {TABLE} AS m SET substitute_of_id = root.professor_id
        FROM session_professors AS sub
        JOIN session_professors AS parent ON parent.id = sub.derived_from_id
        JOIN session_professors AS root ON root.id = coalesce(parent.derived_from_id, parent.id)
        WHERE sub.id = m.session_professor_id AND sub.relation = 'SUBSTITUTE'
    """)

    op.alter_column(TABLE, 'professor_id', nullable=False)
    op.alter_column(TABLE, 'relation', server_default=None)
    op.alter_column(TABLE, 'availability', server_default=None)
    op.create_primary_key('pk_solution_commission_professors', TABLE, ['solution_commission_id', 'professor_id'])
    op.create_foreign_key('fk_solution_commission_professors_solution_commission', TABLE, 'solution_commissions',
                          ['solution_commission_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_solution_commission_professors_session_professor', TABLE, 'session_professors',
                          ['session_professor_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_solution_commission_professors_professor', TABLE, 'professors',
                          ['professor_id'], ['id'])
    op.create_foreign_key('fk_solution_commission_professors_substitute_of', TABLE, 'professors',
                          ['substitute_of_id'], ['id'])


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    # Members whose session professor no longer exists can't be represented in the old schema
    op.execute(f"DELETE FROM {TABLE} WHERE session_professor_id IS NULL")

    op.drop_constraint('fk_solution_commission_professors_substitute_of', TABLE, type_='foreignkey')
    op.drop_constraint('fk_solution_commission_professors_professor', TABLE, type_='foreignkey')
    op.drop_constraint('fk_solution_commission_professors_session_professor', TABLE, type_='foreignkey')
    op.drop_constraint('fk_solution_commission_professors_solution_commission', TABLE, type_='foreignkey')
    op.drop_constraint('pk_solution_commission_professors', TABLE, type_='primary')

    op.drop_column(TABLE, 'availability')
    op.drop_column(TABLE, 'substitute_of_id')
    op.drop_column(TABLE, 'part')
    op.drop_column(TABLE, 'relation')
    op.drop_column(TABLE, 'professor_id')
    op.alter_column(TABLE, 'session_professor_id', new_column_name='professor_id', nullable=False)

    op.create_primary_key('pk_solution_commission_professors', TABLE, ['solution_commission_id', 'professor_id'])
    op.create_foreign_key('fk_solution_commission_professors_solution_commission_i_9d51', TABLE,
                          'solution_commissions', ['solution_commission_id'], ['id'])
    op.create_foreign_key('fk_solution_commission_professors_professor_id_session__4b4e', TABLE,
                          'session_professors', ['professor_id'], ['id'])


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
