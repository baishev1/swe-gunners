"""add assigned seating: venue layouts, seat categories, order item seats, seat holds

Revision ID: 3d7a1c9e5f20
Revises: 9b4e6f1a2c3d
Create Date: 2026-11-24 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3d7a1c9e5f20"
down_revision: str | None = "9b4e6f1a2c3d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("venue", schema=None) as batch_op:
        batch_op.add_column(sa.Column("layout_key", sa.String(length=50), nullable=True))
    with op.batch_alter_table("ticket_type", schema=None) as batch_op:
        batch_op.add_column(sa.Column("seat_category", sa.Integer(), nullable=True))
    with op.batch_alter_table("order_item", schema=None) as batch_op:
        batch_op.add_column(sa.Column("seats", sa.JSON(), server_default="[]", nullable=False))

    op.create_table(
        "seat_hold",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("seat_id", sa.String(length=32), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_type_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"], ["event.id"], name=op.f("fk_seat_hold_event_id_event")
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["order.id"],
            name=op.f("fk_seat_hold_order_id_order"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_seat_hold")),
        sa.UniqueConstraint("event_id", "seat_id", name=op.f("uq_seat_hold_event_id")),
    )
    with op.batch_alter_table("seat_hold", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_seat_hold_event_id"), ["event_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_seat_hold_order_id"), ["order_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("seat_hold", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_seat_hold_order_id"))
        batch_op.drop_index(batch_op.f("ix_seat_hold_event_id"))
    op.drop_table("seat_hold")
    with op.batch_alter_table("order_item", schema=None) as batch_op:
        batch_op.drop_column("seats")
    with op.batch_alter_table("ticket_type", schema=None) as batch_op:
        batch_op.drop_column("seat_category")
    with op.batch_alter_table("venue", schema=None) as batch_op:
        batch_op.drop_column("layout_key")
