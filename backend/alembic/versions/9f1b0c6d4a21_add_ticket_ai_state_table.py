"""add ticket ai state table

Revision ID: 9f1b0c6d4a21
Revises: 4d24c48b3f70
Create Date: 2026-03-26 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


AI_SCHEMA = "AITicketOps"

# revision identifiers, used by Alembic.
revision: str = "9f1b0c6d4a21"
down_revision: Union[str, Sequence[str], None] = "4d24c48b3f70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(f'CREATE SCHEMA IF NOT EXISTS "{AI_SCHEMA}"')
    op.create_table(
        "ticket_ai_state",
        sa.Column("ticket_ai_state_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("autotask_ticket_id", sa.Integer(), nullable=False),
        sa.Column("ticket_number", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("company", sa.Text(), nullable=False),
        sa.Column("contact", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("issue_type", sa.Text(), nullable=False),
        sa.Column("sub_issue_type", sa.Text(), nullable=False),
        sa.Column("queue", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("due_date", sa.Text(), nullable=False),
        sa.Column("primary_resource", sa.Text(), nullable=True),
        sa.Column("secondary_resource", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("priority_label", sa.Text(), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False),
        sa.Column("classification_method", sa.Text(), nullable=False),
        sa.Column(
            "is_closed", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "refreshed_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("ticket_ai_state_id"),
        schema=AI_SCHEMA,
    )
    op.create_index(
        "ix_ticket_ai_state_tenant_ticket",
        "ticket_ai_state",
        ["tenant_id", "autotask_ticket_id"],
        unique=True,
        schema=AI_SCHEMA,
    )
    op.create_index(
        "ix_ticket_ai_state_tenant_status",
        "ticket_ai_state",
        ["tenant_id", "status"],
        unique=False,
        schema=AI_SCHEMA,
    )
    op.create_index(
        "ix_ticket_ai_state_tenant_company",
        "ticket_ai_state",
        ["tenant_id", "company"],
        unique=False,
        schema=AI_SCHEMA,
    )
    op.create_index(
        "ix_ticket_ai_state_tenant_category",
        "ticket_ai_state",
        ["tenant_id", "category"],
        unique=False,
        schema=AI_SCHEMA,
    )
    op.create_index(
        "ix_ticket_ai_state_tenant_closed",
        "ticket_ai_state",
        ["tenant_id", "is_closed"],
        unique=False,
        schema=AI_SCHEMA,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_ticket_ai_state_tenant_closed",
        table_name="ticket_ai_state",
        schema=AI_SCHEMA,
    )
    op.drop_index(
        "ix_ticket_ai_state_tenant_category",
        table_name="ticket_ai_state",
        schema=AI_SCHEMA,
    )
    op.drop_index(
        "ix_ticket_ai_state_tenant_company",
        table_name="ticket_ai_state",
        schema=AI_SCHEMA,
    )
    op.drop_index(
        "ix_ticket_ai_state_tenant_status",
        table_name="ticket_ai_state",
        schema=AI_SCHEMA,
    )
    op.drop_index(
        "ix_ticket_ai_state_tenant_ticket",
        table_name="ticket_ai_state",
        schema=AI_SCHEMA,
    )
    op.drop_table("ticket_ai_state", schema=AI_SCHEMA)
    op.execute(f'DROP SCHEMA IF EXISTS "{AI_SCHEMA}"')
