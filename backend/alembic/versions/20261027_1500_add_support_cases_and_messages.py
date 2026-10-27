"""Add support cases/messages and join the user and ticket-type migration heads.

Revision ID: a18f34d5c902
Revises: bd0c298409ac, 2a15a39c05cd
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a18f34d5c902"
down_revision: tuple[str, str] = ("bd0c298409ac", "2a15a39c05cd")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "support_case",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("requester_id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=True),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("target", sa.String(20), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["requester_id"], ["user.id"],
                                name=op.f("fk_support_case_requester_id_user")),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"],
                                name=op.f("fk_support_case_event_id_event")),
        sa.ForeignKeyConstraint(["assignee_id"], ["user.id"],
                                name=op.f("fk_support_case_assignee_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_support_case")),
    )
    op.create_index(op.f("ix_support_case_requester_id"), "support_case", ["requester_id"])
    op.create_index(op.f("ix_support_case_event_id"), "support_case", ["event_id"])
    op.create_table(
        "support_message",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["support_case.id"],
                                name=op.f("fk_support_message_case_id_support_case")),
        sa.ForeignKeyConstraint(["author_id"], ["user.id"],
                                name=op.f("fk_support_message_author_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_support_message")),
    )
    op.create_index(op.f("ix_support_message_case_id"), "support_message", ["case_id"])


def downgrade() -> None:
    op.drop_table("support_message")
    op.drop_table("support_case")
