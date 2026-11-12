"""add processing fee percent to platform settings

Revision ID: c1d5e8a4b927
Revises: adbd85225fc2
Create Date: 2026-11-12 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c1d5e8a4b927"
down_revision: str | None = "adbd85225fc2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "platform_setting",
        sa.Column(
            "processing_fee_percent", sa.Float(), nullable=False, server_default="3.0"
        ),
    )


def downgrade() -> None:
    with op.batch_alter_table("platform_setting", schema=None) as batch_op:
        batch_op.drop_column("processing_fee_percent")
