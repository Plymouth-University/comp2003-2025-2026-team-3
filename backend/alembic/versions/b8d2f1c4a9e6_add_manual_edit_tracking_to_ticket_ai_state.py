"""add manual edit tracking to ticket_ai_state

Revision ID: b8d2f1c4a9e6
Revises: a7c8d9e0f1a2
Create Date: 2026-04-21 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


AI_SCHEMA = "AITicketOps"

# revision identifiers, used by Alembic.
revision: str = "b8d2f1c4a9e6"
down_revision: Union[str, Sequence[str], None] = "a7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ticket_ai_state",
        sa.Column(
            "manual_edit_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        schema=AI_SCHEMA,
    )
    op.add_column(
        "ticket_ai_state",
        sa.Column(
            "manual_edit_set_by_profile_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        schema=AI_SCHEMA,
    )
    op.add_column(
        "ticket_ai_state",
        sa.Column("manual_edit_set_at", sa.TIMESTAMP(timezone=True), nullable=True),
        schema=AI_SCHEMA,
    )
    op.create_foreign_key(
        "fk_ticket_ai_state_manual_edit_set_by_profile",
        "ticket_ai_state",
        "profile",
        ["manual_edit_set_by_profile_id"],
        ["profile_id"],
        ondelete="SET NULL",
        source_schema=AI_SCHEMA,
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_ticket_ai_state_manual_edit_set_by_profile",
        "ticket_ai_state",
        type_="foreignkey",
        schema=AI_SCHEMA,
    )
    op.drop_column("ticket_ai_state", "manual_edit_set_at", schema=AI_SCHEMA)
    op.drop_column(
        "ticket_ai_state", "manual_edit_set_by_profile_id", schema=AI_SCHEMA
    )
    op.drop_column("ticket_ai_state", "manual_edit_fields", schema=AI_SCHEMA)
