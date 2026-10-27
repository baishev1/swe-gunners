"""merge user and ticket type branches

Revision ID: 26e8e8214d0f
Revises: bd0c298409ac, 810dbae96295
Create Date: 2026-10-27 14:50:01.147886
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "26e8e8214d0f"
down_revision: str | None = ("bd0c298409ac", "810dbae96295")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
