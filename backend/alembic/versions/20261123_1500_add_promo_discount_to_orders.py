"""add promo discount to orders

Revision ID: 7c1e2d9a4b10
Revises: 64894ef46efa
Create Date: 2026-11-23 15:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "7c1e2d9a4b10"
down_revision: str | None = "64894ef46efa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("order", schema=None) as batch_op:
        batch_op.add_column(sa.Column("promo_campaign_id", sa.Uuid(), nullable=True))
        batch_op.add_column(
            sa.Column("discount_kzt", sa.Integer(), nullable=False, server_default="0")
        )


def downgrade() -> None:
    with op.batch_alter_table("order", schema=None) as batch_op:
        batch_op.drop_column("discount_kzt")
        batch_op.drop_column("promo_campaign_id")
