"""merge staff and payments migration branches

Revision ID: f3a8c1e5b7d9
Revises: e2b7c4d9f1a3, b20938dea568
Create Date: 2026-10-27 16:12:00
"""

from collections.abc import Sequence


revision: str = "f3a8c1e5b7d9"
down_revision: tuple[str, str] = ("e2b7c4d9f1a3", "b20938dea568")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
