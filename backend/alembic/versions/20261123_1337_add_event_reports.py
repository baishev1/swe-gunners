"""add event reports

Revision ID: 64894ef46efa
Revises: f03fa5ede64d
Create Date: 2026-11-23 13:37:14.984491
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "64894ef46efa"
down_revision: str | None = "f03fa5ede64d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_report",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("reporter_id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"], ["event.id"], name=op.f("fk_event_report_event_id_event")
        ),
        sa.ForeignKeyConstraint(
            ["reporter_id"], ["user.id"], name=op.f("fk_event_report_reporter_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_report")),
    )
    with op.batch_alter_table("event_report", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_event_report_event_id"), ["event_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("event_report", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_event_report_event_id"))

    op.drop_table("event_report")