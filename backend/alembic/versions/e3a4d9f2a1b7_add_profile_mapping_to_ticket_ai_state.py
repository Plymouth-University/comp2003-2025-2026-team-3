"""add profile mapping to ticket ai state

Revision ID: e3a4d9f2a1b7
Revises: 9f1b0c6d4a21
Create Date: 2026-03-26 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e3a4d9f2a1b7"
down_revision: Union[str, Sequence[str], None] = "9f1b0c6d4a21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "ticket_ai_state",
        sa.Column("primary_profile_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "ticket_ai_state",
        sa.Column("secondary_profile_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_ticket_ai_state_primary_profile",
        "ticket_ai_state",
        "profile",
        ["primary_profile_id"],
        ["profile_id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_ticket_ai_state_secondary_profile",
        "ticket_ai_state",
        "profile",
        ["secondary_profile_id"],
        ["profile_id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_ticket_ai_state_tenant_primary_profile",
        "ticket_ai_state",
        ["tenant_id", "primary_profile_id"],
        unique=False,
    )
    op.create_index(
        "ix_ticket_ai_state_tenant_secondary_profile",
        "ticket_ai_state",
        ["tenant_id", "secondary_profile_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_ticket_ai_state_tenant_secondary_profile", table_name="ticket_ai_state")
    op.drop_index("ix_ticket_ai_state_tenant_primary_profile", table_name="ticket_ai_state")
    op.drop_constraint("fk_ticket_ai_state_secondary_profile", "ticket_ai_state", type_="foreignkey")
    op.drop_constraint("fk_ticket_ai_state_primary_profile", "ticket_ai_state", type_="foreignkey")
    op.drop_column("ticket_ai_state", "secondary_profile_id")
    op.drop_column("ticket_ai_state", "primary_profile_id")
