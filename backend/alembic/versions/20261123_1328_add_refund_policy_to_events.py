"""add refund policy to events

Revision ID: f03fa5ede64d
Revises: c1d5e8a4b927
Create Date: 2026-11-23 13:28:53.768321
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f03fa5ede64d"
down_revision: str | None = "c1d5e8a4b927"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.add_column(sa.Column("refund_policy", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.drop_column("refund_policy")
