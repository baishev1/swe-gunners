"""merge auth and part 5 migrations

Revision ID: 44ed9f7b380a
Revises: 26e8e8214d0f, b7f238c2d559
Create Date: 2026-10-27 15:08:50.972678
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "44ed9f7b380a"
down_revision: str | None = ("26e8e8214d0f", "b7f238c2d559")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
