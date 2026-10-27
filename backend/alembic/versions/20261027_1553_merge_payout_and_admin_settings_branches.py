"""merge payout and admin settings branches

Revision ID: 9cdaedba0046
Revises: 1692d46c0778, 5ec8138f57f2
Create Date: 2026-10-27 15:53:48.744519
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "9cdaedba0046"
down_revision: str | None = ("1692d46c0778", "5ec8138f57f2")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
