"""add order and ticket context to support cases

Revision ID: 3e7a9c1d5f20
Revises: 9d4f1a2b3c55
Create Date: 2026-11-24 10:10:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "3e7a9c1d5f20"
down_revision: str | None = "9d4f1a2b3c55"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("support_case", schema=None) as batch_op:
        batch_op.add_column(sa.Column("order_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("ticket_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_support_case_order_id_order", "order", ["order_id"], ["id"]
        )
        batch_op.create_foreign_key(
            "fk_support_case_ticket_id_ticket", "ticket", ["ticket_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("support_case", schema=None) as batch_op:
        batch_op.drop_constraint("fk_support_case_ticket_id_ticket", type_="foreignkey")
        batch_op.drop_constraint("fk_support_case_order_id_order", type_="foreignkey")
        batch_op.drop_column("ticket_id")
        batch_op.drop_column("order_id")
