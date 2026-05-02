"""add category override fields to ticket_ai_state

Revision ID: e92b1f4c6a30
Revises: d5e7f2a8c9b1
Create Date: 2026-04-22 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


AI_SCHEMA = "AITicketOps"

# revision identifiers, used by Alembic.
revision: str = "e92b1f4c6a30"
down_revision: Union[str, Sequence[str], None] = "d5e7f2a8c9b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ticket_ai_state",
        sa.Column("category_override_reason", sa.Text(), nullable=True),
        schema=AI_SCHEMA,
    )
    op.add_column(
        "ticket_ai_state",
        sa.Column("category_override_set_at", sa.TIMESTAMP(timezone=True), nullable=True),
        schema=AI_SCHEMA,
    )


def downgrade() -> None:
    op.drop_column("ticket_ai_state", "category_override_set_at", schema=AI_SCHEMA)
    op.drop_column("ticket_ai_state", "category_override_reason", schema=AI_SCHEMA)
