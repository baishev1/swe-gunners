"""Predefined venue layouts for assigned seating (SRS 4.3.1).

The MVP ships one layout and no layout editor: organizers pick it through a venue that
carries its key. Seats are numbered continuously across a row, from the right-hand block
to the left one, so a row's ranges below never overlap between blocks of the same tier.
"""

from dataclasses import dataclass, field
from functools import cached_property


@dataclass(frozen=True)
class LayoutRow:
    label: str
    first: int
    last: int

    @property
    def numbers(self) -> range:
        return range(self.first, self.last + 1)


@dataclass(frozen=True)
class LayoutSection:
    key: str
    name: str
    tier: str  # balcony | upper | lower, top to bottom as drawn
    column: int  # 0 left, 1 centre, 2 right
    category: int
    rows: tuple[LayoutRow, ...]


@dataclass(frozen=True)
class LayoutCategory:
    category: int
    name: str


@dataclass(frozen=True)
class LayoutSeat:
    id: str
    section: LayoutSection
    row: str
    number: int
    accessible: bool


@dataclass(frozen=True)
class VenueLayout:
    key: str
    name: str
    stage: str  # where the stage is drawn relative to the seats
    categories: tuple[LayoutCategory, ...]
    sections: tuple[LayoutSection, ...]
    accessible_seats: frozenset[str] = field(default_factory=frozenset)

    @cached_property
    def seats(self) -> dict[str, LayoutSeat]:
        seats: dict[str, LayoutSeat] = {}
        for section in self.sections:
            for row in section.rows:
                for number in row.numbers:
                    seat_id = seat_key(section.key, row.label, number)
                    seats[seat_id] = LayoutSeat(
                        id=seat_id,
                        section=section,
                        row=row.label,
                        number=number,
                        accessible=seat_id in self.accessible_seats,
                    )
        return seats

    def seat_count(self, category: int | None = None) -> int:
        return sum(
            1
            for seat in self.seats.values()
            if category is None or seat.section.category == category
        )


def seat_key(section: str, row: str, number: int) -> str:
    return f"{section}-{row}-{number}"


def _rows(*rows: tuple[str, int, int]) -> tuple[LayoutRow, ...]:
    return tuple(LayoutRow(label, first, last) for label, first, last in rows)


MAIN_HALL = VenueLayout(
    key="main_hall",
    name="Main Hall",
    stage="bottom",
    categories=(
        LayoutCategory(1, "Lower parterre"),
        LayoutCategory(2, "Upper parterre"),
        LayoutCategory(3, "Balcony"),
    ),
    sections=(
        LayoutSection(
            "BL",
            "Balcony left",
            "balcony",
            0,
            3,
            _rows(
                ("P", 19, 27),
                ("O", 30, 40),
                ("N", 32, 43),
                ("M", 30, 40),
                ("L", 32, 43),
                ("K", 30, 40),
                ("J", 31, 42),
            ),
        ),
        LayoutSection(
            "BC",
            "Balcony centre",
            "balcony",
            1,
            3,
            _rows(
                ("P", 10, 18),
                ("O", 12, 29),
                ("N", 13, 31),
                ("M", 12, 29),
                ("L", 13, 31),
                ("K", 12, 29),
                ("J", 12, 30),
            ),
        ),
        LayoutSection(
            "BR",
            "Balcony right",
            "balcony",
            2,
            3,
            _rows(
                ("P", 1, 9),
                ("O", 1, 11),
                ("N", 1, 12),
                ("M", 1, 11),
                ("L", 1, 12),
                ("K", 1, 11),
                ("J", 1, 11),
            ),
        ),
        LayoutSection(
            "A",
            "A",
            "upper",
            0,
            2,
            _rows(
                ("U", 14, 27),
                ("T", 15, 28),
                ("S", 29, 41),
                ("R", 28, 40),
                ("Q", 29, 41),
                ("P", 27, 38),
                ("O", 28, 39),
                ("N", 27, 37),
                ("M", 28, 39),
                ("L", 26, 33),
            ),
        ),
        LayoutSection(
            "B",
            "B",
            "upper",
            1,
            2,
            _rows(
                ("S", 14, 28),
                ("R", 14, 27),
                ("Q", 14, 28),
                ("P", 13, 26),
                ("O", 13, 27),
                ("N", 13, 26),
                ("M", 13, 27),
                ("L", 12, 25),
            ),
        ),
        LayoutSection(
            "C",
            "C",
            "upper",
            2,
            2,
            _rows(
                ("U", 1, 13),
                ("T", 1, 14),
                ("S", 1, 13),
                ("R", 1, 13),
                ("Q", 1, 13),
                ("P", 1, 12),
                ("O", 1, 12),
                ("N", 1, 12),
                ("M", 1, 12),
                ("L", 1, 11),
            ),
        ),
        LayoutSection(
            "D",
            "D",
            "lower",
            0,
            1,
            _rows(
                ("K", 27, 34),
                ("J", 25, 34),
                ("I", 26, 35),
                ("H", 25, 34),
                ("G", 26, 35),
                ("F", 24, 32),
                ("E", 25, 33),
                ("D", 24, 32),
                ("C", 24, 31),
                ("B", 24, 31),
                ("A", 24, 31),
            ),
        ),
        LayoutSection(
            "E",
            "E",
            "lower",
            1,
            1,
            _rows(
                ("K", 12, 26),
                ("J", 11, 24),
                ("I", 11, 25),
                ("H", 11, 24),
                ("G", 11, 25),
                ("F", 10, 23),
                ("E", 10, 24),
                ("D", 10, 23),
                ("C", 9, 23),
                ("B", 10, 23),
                ("A", 9, 23),
            ),
        ),
        LayoutSection(
            "F",
            "F",
            "lower",
            2,
            1,
            _rows(
                ("K", 1, 11),
                ("J", 1, 10),
                ("I", 1, 10),
                ("H", 1, 10),
                ("G", 1, 10),
                ("F", 1, 9),
                ("E", 1, 9),
                ("D", 1, 9),
                ("C", 1, 8),
                ("B", 1, 9),
                ("A", 1, 8),
            ),
        ),
    ),
    # Front-row aisle seats next to the centre block.
    accessible_seats=frozenset({"D-A-24", "D-A-25", "F-A-7", "F-A-8"}),
)

LAYOUTS: dict[str, VenueLayout] = {MAIN_HALL.key: MAIN_HALL}


def get_layout(key: str | None) -> VenueLayout | None:
    return LAYOUTS.get(key) if key else None
