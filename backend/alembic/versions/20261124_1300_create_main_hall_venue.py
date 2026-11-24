"""create the Main Hall venue for the predefined seating layout

Revision ID: 6e2b8f4a1d93
Revises: 3d7a1c9e5f20
Create Date: 2026-11-24 13:00:00.000000

The layout itself lives in code (features/seating/layouts.py). Creating its venue here
means every environment can pick Main Hall for an assigned-seating event without seeding.
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "6e2b8f4a1d93"
down_revision: str | None = "3d7a1c9e5f20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

venue = sa.table(
    "venue",
    sa.column("id", sa.Uuid()),
    sa.column("name", sa.String()),
    sa.column("address", sa.String()),
    sa.column("layout_key", sa.String()),
    sa.column("created_at", sa.DateTime()),
    sa.column("updated_at", sa.DateTime()),
)


def upgrade() -> None:
    connection = op.get_bind()
    exists = connection.execute(
        sa.select(venue.c.id).where(venue.c.layout_key == "main_hall")
    ).first()
    if exists is None:
        now = datetime.now(UTC).replace(tzinfo=None)
        op.bulk_insert(
            venue,
            [
                {
                    "id": uuid4(),
                    "name": "Main Hall",
                    "address": "53 Kabanbay Batyr Ave, Astana",
                    "layout_key": "main_hall",
                    "created_at": now,
                    "updated_at": now,
                }
            ],
        )


def downgrade() -> None:
    # Leave the venue alone if events already use it.
    connection = op.get_bind()
    used = connection.execute(
        sa.text(
            "SELECT 1 FROM event JOIN venue ON venue.id = event.venue_id "
            "WHERE venue.layout_key = 'main_hall' LIMIT 1"
        )
    ).first()
    if used is None:
        op.execute(venue.delete().where(venue.c.layout_key == "main_hall"))
