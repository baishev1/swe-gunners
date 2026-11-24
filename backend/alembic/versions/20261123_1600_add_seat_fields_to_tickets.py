"""add seat fields to tickets

Revision ID: 9b4e6f1a2c3d
Revises: 7c1e2d9a4b10
Create Date: 2026-11-23 16:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9b4e6f1a2c3d"
down_revision: str | None = "7c1e2d9a4b10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("ticket", schema=None) as batch_op:
        batch_op.add_column(sa.Column("section", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("row", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("seat", sa.String(length=50), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("ticket", schema=None) as batch_op:
        batch_op.drop_column("seat")
        batch_op.drop_column("row")
        batch_op.drop_column("section")
