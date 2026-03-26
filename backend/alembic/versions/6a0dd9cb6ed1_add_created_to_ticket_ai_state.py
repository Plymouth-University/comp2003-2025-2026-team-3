"""add created to ticket ai state

Revision ID: 6a0dd9cb6ed1
Revises: e3a4d9f2a1b7
Create Date: 2026-03-26 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6a0dd9cb6ed1"
down_revision: Union[str, Sequence[str], None] = "e3a4d9f2a1b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "ticket_ai_state",
        sa.Column("created", sa.Text(), nullable=True),
    )
    op.execute("UPDATE ticket_ai_state SET created = refreshed_at::text WHERE created IS NULL")
    op.alter_column("ticket_ai_state", "created", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ticket_ai_state", "created")
