"""link event to organizer

Revision ID: ddc0336c53cc
Revises: 26e8e8214d0f
Create Date: 2026-10-27 14:58:24.417102
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "ddc0336c53cc"
down_revision: str | None = "26e8e8214d0f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        'DELETE FROM ticket_type WHERE event_id IN (SELECT id FROM event '
        'WHERE organizer_id NOT IN (SELECT id FROM "user"))'
    )
    op.execute('DELETE FROM event WHERE organizer_id NOT IN (SELECT id FROM "user")')
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.create_foreign_key(
            batch_op.f("fk_event_organizer_id_user"), "user", ["organizer_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_event_organizer_id_user"), type_="foreignkey")
