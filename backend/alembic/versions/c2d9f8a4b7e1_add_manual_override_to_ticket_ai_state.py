"""add manual override fields to ticket_ai_state

Revision ID: c2d9f8a4b7e1
Revises: 6a0dd9cb6ed1
Create Date: 2026-03-26 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


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
    )
    op.add_column(
        "ticket_ai_state",
        sa.Column(
            "manual_override_set_by_profile_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "ticket_ai_state",
        sa.Column("manual_override_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "ticket_ai_state",
        sa.Column("manual_override_set_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_ticket_ai_state_manual_override_profile",
        "ticket_ai_state",
        "profile",
        ["manual_override_profile_id"],
        ["profile_id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_ticket_ai_state_manual_override_set_by_profile",
        "ticket_ai_state",
        "profile",
        ["manual_override_set_by_profile_id"],
        ["profile_id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_ticket_ai_state_tenant_manual_override_profile",
        "ticket_ai_state",
        ["tenant_id", "manual_override_profile_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ticket_ai_state_tenant_manual_override_profile",
        table_name="ticket_ai_state",
    )
    op.drop_constraint(
        "fk_ticket_ai_state_manual_override_set_by_profile",
        "ticket_ai_state",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_ticket_ai_state_manual_override_profile",
        "ticket_ai_state",
        type_="foreignkey",
    )
    op.drop_column("ticket_ai_state", "manual_override_set_at")
    op.drop_column("ticket_ai_state", "manual_override_reason")
    op.drop_column("ticket_ai_state", "manual_override_set_by_profile_id")
    op.drop_column("ticket_ai_state", "manual_override_profile_id")
