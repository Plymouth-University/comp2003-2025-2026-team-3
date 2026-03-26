"""add ai managed assignment fields to ticket_ai_state

Revision ID: f4a1c2b3d4e5
Revises: c2d9f8a4b7e1
Create Date: 2026-03-26 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f4a1c2b3d4e5"
down_revision: Union[str, Sequence[str], None] = "c2d9f8a4b7e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ticket_ai_state",
        sa.Column("ai_managed_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "ticket_ai_state",
        sa.Column("ai_managed_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "ticket_ai_state",
        sa.Column("ai_managed_set_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_ticket_ai_state_ai_managed_profile",
        "ticket_ai_state",
        "profile",
        ["ai_managed_profile_id"],
        ["profile_id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_ticket_ai_state_ai_managed_profile", "ticket_ai_state", type_="foreignkey")
    op.drop_column("ticket_ai_state", "ai_managed_set_at")
    op.drop_column("ticket_ai_state", "ai_managed_reason")
    op.drop_column("ticket_ai_state", "ai_managed_profile_id")
