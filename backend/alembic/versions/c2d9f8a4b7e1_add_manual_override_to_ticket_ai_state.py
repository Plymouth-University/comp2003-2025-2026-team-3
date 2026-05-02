"""add manual override fields to ticket_ai_state

Revision ID: c2d9f8a4b7e1
Revises: 6a0dd9cb6ed1
Create Date: 2026-03-26 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


AI_SCHEMA = "AITicketOps"

# revision identifiers, used by Alembic.
revision: str = "c2d9f8a4b7e1"
down_revision: Union[str, Sequence[str], None] = "6a0dd9cb6ed1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ticket_ai_state",
        sa.Column(
            "manual_override_profile_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        schema=AI_SCHEMA,
    )
    op.add_column(
        "ticket_ai_state",
        sa.Column(
            "manual_override_set_by_profile_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        schema=AI_SCHEMA,
    )
    op.add_column(
        "ticket_ai_state",
        sa.Column("manual_override_reason", sa.Text(), nullable=True),
        schema=AI_SCHEMA,
    )
    op.add_column(
        "ticket_ai_state",
        sa.Column("manual_override_set_at", sa.TIMESTAMP(timezone=True), nullable=True),
        schema=AI_SCHEMA,
    )
    op.create_foreign_key(
        "fk_ticket_ai_state_manual_override_profile",
        "ticket_ai_state",
        "profile",
        ["manual_override_profile_id"],
        ["profile_id"],
        ondelete="SET NULL",
        source_schema=AI_SCHEMA,
    )
    op.create_foreign_key(
        "fk_ticket_ai_state_manual_override_set_by_profile",
        "ticket_ai_state",
        "profile",
        ["manual_override_set_by_profile_id"],
        ["profile_id"],
        ondelete="SET NULL",
        source_schema=AI_SCHEMA,
    )
    op.create_index(
        "ix_ticket_ai_state_tenant_manual_override_profile",
        "ticket_ai_state",
        ["tenant_id", "manual_override_profile_id"],
        unique=False,
        schema=AI_SCHEMA,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ticket_ai_state_tenant_manual_override_profile",
        table_name="ticket_ai_state",
        schema=AI_SCHEMA,
    )
    op.drop_constraint(
        "fk_ticket_ai_state_manual_override_set_by_profile",
        "ticket_ai_state",
        type_="foreignkey",
        schema=AI_SCHEMA,
    )
    op.drop_constraint(
        "fk_ticket_ai_state_manual_override_profile",
        "ticket_ai_state",
        type_="foreignkey",
        schema=AI_SCHEMA,
    )
    op.drop_column("ticket_ai_state", "manual_override_set_at", schema=AI_SCHEMA)
    op.drop_column("ticket_ai_state", "manual_override_reason", schema=AI_SCHEMA)
    op.drop_column(
        "ticket_ai_state", "manual_override_set_by_profile_id", schema=AI_SCHEMA
    )
    op.drop_column("ticket_ai_state", "manual_override_profile_id", schema=AI_SCHEMA)
