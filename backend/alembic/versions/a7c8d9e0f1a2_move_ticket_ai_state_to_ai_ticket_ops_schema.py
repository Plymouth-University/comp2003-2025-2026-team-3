"""move ticket ai state to AITicketOps schema

Revision ID: a7c8d9e0f1a2
Revises: f4a1c2b3d4e5
Create Date: 2026-04-21 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "a7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "f4a1c2b3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


AI_SCHEMA = "AITicketOps"


def upgrade() -> None:
    """Ensure legacy public ticket_ai_state lives in the AI schema."""
    op.execute(f'CREATE SCHEMA IF NOT EXISTS "{AI_SCHEMA}"')
    op.execute(
        f"""
        DO $$
        BEGIN
            IF to_regclass('public.ticket_ai_state') IS NOT NULL
               AND to_regclass('"{AI_SCHEMA}".ticket_ai_state') IS NULL THEN
                ALTER TABLE public.ticket_ai_state SET SCHEMA "{AI_SCHEMA}";
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Move ticket_ai_state back to public for downgrade compatibility."""
    op.execute(
        f"""
        DO $$
        BEGIN
            IF to_regclass('"{AI_SCHEMA}".ticket_ai_state') IS NOT NULL
               AND to_regclass('public.ticket_ai_state') IS NULL THEN
                ALTER TABLE "{AI_SCHEMA}".ticket_ai_state SET SCHEMA public;
            END IF;
        END $$;
        """
    )
