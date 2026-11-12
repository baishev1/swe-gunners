"""merge check-in and payout migration branches

Revision ID: 7f4c9d2a1e6b
Revises: 44ed9f7b380a, 1692d46c0778
Create Date: 2026-10-27 15:52:00
"""

from collections.abc import Sequence


revision: str = "7f4c9d2a1e6b"
down_revision: tuple[str, str] = ("44ed9f7b380a", "1692d46c0778")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
