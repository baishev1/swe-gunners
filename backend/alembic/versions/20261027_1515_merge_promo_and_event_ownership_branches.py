"""merge promo and event ownership branches

Revision ID: 9be22e2351f6
Revises: c6313738dbdf, ddc0336c53cc
Create Date: 2026-10-27 15:15:23.716050
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "9be22e2351f6"
down_revision: str | None = ("c6313738dbdf", "ddc0336c53cc")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
