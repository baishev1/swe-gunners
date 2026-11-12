"""merge check-in and admin migration branches

Revision ID: e2b7c4d9f1a3
Revises: 7f4c9d2a1e6b, 9cdaedba0046
Create Date: 2026-10-27 15:58:00
"""

from collections.abc import Sequence


revision: str = "e2b7c4d9f1a3"
down_revision: tuple[str, str] = ("7f4c9d2a1e6b", "9cdaedba0046")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
