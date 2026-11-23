"""remember an event's status before an admin suspension

Revision ID: 5b8c2d4e6f71
Revises: 3e7a9c1d5f20
Create Date: 2026-11-24 10:20:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "5b8c2d4e6f71"
down_revision: str | None = "3e7a9c1d5f20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("status_before_suspension", sa.String(length=20), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.drop_column("status_before_suspension")
