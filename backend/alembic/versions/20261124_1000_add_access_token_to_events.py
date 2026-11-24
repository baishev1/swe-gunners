"""add access token to events

Revision ID: 9d4f1a2b3c55
Revises: 7c1e2d9a4b10
Create Date: 2026-11-24 10:00:00.000000
"""

import secrets
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "9d4f1a2b3c55"
down_revision: str | None = "7c1e2d9a4b10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.add_column(sa.Column("access_token", sa.String(length=64), nullable=True))
        batch_op.create_index("ix_event_access_token", ["access_token"], unique=False)

    # Existing events get their own secret so private ones can be shared right away.
    bind = op.get_bind()
    event = sa.table("event", sa.column("id", sa.Uuid()), sa.column("access_token", sa.String()))
    for (event_id,) in bind.execute(sa.select(event.c.id)).all():
        bind.execute(
            event.update()
            .where(event.c.id == event_id)
            .values(access_token=secrets.token_urlsafe(24))
        )


def downgrade() -> None:
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.drop_index("ix_event_access_token")
        batch_op.drop_column("access_token")
