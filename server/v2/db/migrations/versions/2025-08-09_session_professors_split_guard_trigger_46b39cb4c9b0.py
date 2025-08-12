"""session_professors split‐guard trigger

Revision ID: 46b39cb4c9b0
Revises: 9f68d04a05bc
Create Date: 2025-08-09 00:11:34.902884

"""

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from advanced_alchemy.types import EncryptedString, EncryptedText, GUID, ORA_JSONB, DateTimeUTC, StoredObject, \
    PasswordHash
from sqlalchemy import Text  # noqa: F401

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
revision = '46b39cb4c9b0'
down_revision = '9f68d04a05bc'
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


split_trigger_ddl = (
    """
    CREATE OR REPLACE FUNCTION trg_session_professors_guard_split()
        RETURNS trigger
        LANGUAGE plpgsql
    AS
    $$
    DECLARE
        parent_rel text;
    BEGIN
        -- Child-side validation
        IF NEW.derived_from_id IS NOT NULL THEN
            SELECT (p.relation)::text
            INTO parent_rel
            FROM session_professors p
            WHERE p.id = NEW.derived_from_id;

            -- Forbid: SPLIT child under SPLIT or SUBSTITUTE parent
            IF (NEW.relation)::text = 'SPLIT' AND parent_rel IN ('SPLIT', 'SUBSTITUTE') THEN
                RAISE EXCEPTION 'Invalid relationship: a SPLIT child cannot be under a % parent (child id %, parent id %)',
                    parent_rel, COALESCE(NEW.id, 0), NEW.derived_from_id
                    USING ERRCODE = '23514',
                        CONSTRAINT = 'chk_no_split_under_split_or_sub';
            END IF;

            -- Forbid: SUBSTITUTE child under SUBSTITUTE parent
            IF (NEW.relation)::text = 'SUBSTITUTE' AND parent_rel = 'SUBSTITUTE' THEN
                RAISE EXCEPTION 'Invalid relationship: a SUBSTITUTE child cannot be under a SUBSTITUTE parent (child id %, parent id %)',
                    COALESCE(NEW.id, 0), NEW.derived_from_id
                    USING ERRCODE = '23514',
                        CONSTRAINT = 'chk_no_sub_under_sub';
            END IF;

            -- NEW: Forbid adding a SUBSTITUTE if the parent already has ANY children (SPLIT or SUBSTITUTE)
            IF (NEW.relation)::text = 'SUBSTITUTE' THEN
                IF EXISTS (
                    SELECT 1
                    FROM session_professors c
                    WHERE c.derived_from_id = NEW.derived_from_id
                      AND c.id IS DISTINCT FROM NEW.id
                ) THEN
                    RAISE EXCEPTION 'Invalid relationship: cannot add a SUBSTITUTE under a parent (id %) that already has derived entries',
                        NEW.derived_from_id
                        USING ERRCODE = '23514',
                            CONSTRAINT = 'chk_no_sub_when_children_exist';
                END IF;
            END IF;

            -- NEW: Forbid adding a SPLIT if the parent already has a SUBSTITUTE child
            IF (NEW.relation)::text = 'SPLIT' THEN
                IF EXISTS (
                    SELECT 1
                    FROM session_professors c
                    WHERE c.derived_from_id = NEW.derived_from_id
                      AND (c.relation)::text = 'SUBSTITUTE'
                      AND c.id IS DISTINCT FROM NEW.id
                ) THEN
                    RAISE EXCEPTION 'Invalid relationship: cannot add a SPLIT under a parent (id %) that already has a SUBSTITUTE',
                        NEW.derived_from_id
                        USING ERRCODE = '23514',
                            CONSTRAINT = 'chk_no_split_when_sub_exists';
                END IF;
            END IF;
        END IF;

        -- Parent-side validation
        -- If this row is being set to SPLIT or SUBSTITUTE, ensure it has no invalid children
        IF (NEW.relation)::text IN ('SPLIT', 'SUBSTITUTE') THEN
            PERFORM 1
            FROM session_professors c
            WHERE c.derived_from_id = NEW.id
              AND (
                -- If parent becomes SPLIT, it cannot have SPLIT children
                ((NEW.relation)::text = 'SPLIT' AND (c.relation)::text = 'SPLIT')
                    OR
                    -- If parent becomes SUBSTITUTE, it cannot have SPLIT or SUBSTITUTE children
                ((NEW.relation)::text = 'SUBSTITUTE' AND (c.relation)::text IN ('SPLIT', 'SUBSTITUTE'))
                )
            LIMIT 1;

            IF FOUND THEN
                RAISE EXCEPTION 'Invalid relationship: cannot set parent id % to % while it has conflicting children',
                    NEW.id, (NEW.relation)::text
                    USING ERRCODE = '23514',
                        CONSTRAINT = 'chk_no_invalid_children_for_parent';
            END IF;
        END IF;

        RETURN NEW;
    END;
    $$;

    CREATE OR REPLACE TRIGGER trg_session_professors_guard_split
        BEFORE INSERT OR UPDATE OF relation, derived_from_id
        ON session_professors
        FOR EACH ROW
    EXECUTE FUNCTION trg_session_professors_guard_split(); \
    """
)

split_drop_ddl = (
    """
    DROP TRIGGER IF EXISTS trg_session_professors_guard_split ON session_professors;
    DROP FUNCTION IF EXISTS trg_session_professors_guard_split(); \
    """
)

prof_owner_trigger_ddl = (
    """
    -- Forbid assigning a supervisor that has any derived entries
    -- (children = splits or substitutes)
    CREATE OR REPLACE FUNCTION session_entries_guard_supervisor_leaf()
        RETURNS trigger
        LANGUAGE plpgsql
    AS
    $$
    BEGIN
        -- Skip when supervisor_id is unchanged in UPDATE
        IF TG_OP = 'UPDATE' AND NEW.supervisor_id IS NOT DISTINCT FROM OLD.supervisor_id THEN
            RETURN NEW;
        END IF;

        -- If somehow NULL arrives, let FK/NOT NULL handle it (or early return)
        IF NEW.supervisor_id IS NULL THEN
            RETURN NEW;
        END IF;

        -- Reject if there is at least one child row derived from this supervisor
        IF EXISTS (SELECT 1
                   FROM session_professors child
                   WHERE child.derived_from_id = NEW.supervisor_id) THEN
            RAISE EXCEPTION
                'The selected supervisor (session_professors.id=%) has derived entries (substitutes or splits). Assign one of its derived entries instead.',
                NEW.supervisor_id
                USING ERRCODE = '23514'; -- check_violation
        END IF;

        RETURN NEW;
    END;
    $$;

    -- Create (or replace) the trigger
    DROP TRIGGER IF EXISTS trg_session_entries_guard_supervisor ON session_entries;

    CREATE CONSTRAINT TRIGGER trg_session_entries_guard_supervisor
        AFTER INSERT OR UPDATE OF supervisor_id
        ON session_entries
        DEFERRABLE INITIALLY DEFERRED 
        FOR EACH ROW
    EXECUTE FUNCTION session_entries_guard_supervisor_leaf(); \
    """
)
prof_owner_trigger_drop = (
    """
    DROP TRIGGER IF EXISTS trg_session_entries_guard_supervisor ON session_entries;
    DROP FUNCTION IF EXISTS session_entries_guard_supervisor_leaf; \
    """
)


def schema_upgrades() -> None:
    """schema upgrade migrations go here."""
    op.execute(split_trigger_ddl)
    op.execute(prof_owner_trigger_ddl)


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.execute(split_drop_ddl)
    op.execute(prof_owner_trigger_drop)


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
