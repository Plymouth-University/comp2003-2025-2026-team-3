"""add reason_closed to ticket_ai_state

Revision ID: d5e7f2a8c9b1
Revises: b8d2f1c4a9e6
Create Date: 2026-04-22 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


AI_SCHEMA = "AITicketOps"

# revision identifiers, used by Alembic.
revision: str = "d5e7f2a8c9b1"
down_revision: Union[str, Sequence[str], None] = "b8d2f1c4a9e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ticket_ai_state",
        sa.Column("reason_closed", sa.Text(), nullable=True),
        schema=AI_SCHEMA,
    )


def downgrade() -> None:
    op.drop_column("ticket_ai_state", "reason_closed", schema=AI_SCHEMA)
