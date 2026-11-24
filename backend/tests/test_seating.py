"""Assigned seating with the predefined Main Hall layout (SRS 4.3.1, UC8)."""

import base64
import re
import zlib
from datetime import UTC, datetime, timedelta

import pytest
from conftest import complete_activation_checklist
from fastapi.testclient import TestClient
from httpx import Response
from test_checkout_holds import age_order

from core import settings
from features.seating.layouts import MAIN_HALL

PRICES = {1: 1_200_000, 2: 800_000, 3: 450_000}


def create_seated_event(
    client: TestClient, headers: dict[str, str], prices: dict[int, int] = PRICES
) -> str:
    venue = client.post(
        "/api/v1/venues",
        json={"name": "Main Hall", "address": "Almaty", "layout_key": "main_hall"},
        headers=headers,
    )
    assert venue.status_code == 201
    now = datetime.now(UTC)
    event_id = client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": "Seated Concert",
            "category": "Music",
            "venue_id": venue.json()["id"],
            "start_time": (now + timedelta(days=10)).isoformat(),
            "end_time": (now + timedelta(days=10, hours=2)).isoformat(),
            "capacity": 100,
        },
    ).json()["id"]
    setup = client.post(
        f"/api/v1/seating/setup?event_id={event_id}",
        headers=headers,
        json={
            "categories": [
                {"category": c, "name": f"Category {c}", "price": price}
                for c, price in prices.items()
            ]
        },
    )
    assert setup.status_code == 200, setup.text
    client.post(f"/api/v1/events/publish?event_id={event_id}", headers=headers)
    if any(prices.values()):
        complete_activation_checklist(client, headers, event_id)
        client.post(f"/api/v1/paid-sales/activate?event_id={event_id}", headers=headers)
    return event_id


@pytest.fixture
def seated_event_id(client: TestClient, organizer_headers: dict[str, str]) -> str:
    return create_seated_event(client, organizer_headers)


def seat_map(client: TestClient, event_id: str) -> dict:
    res = client.get(f"/api/v1/seating/map?event_id={event_id}")
    assert res.status_code == 200, res.text
    return res.json()


def seat_status(client: TestClient, event_id: str, seat_id: str) -> str:
    for section in seat_map(client, event_id)["sections"]:
        for row in section["rows"]:
            for seat in row["seats"]:
                if seat["id"] == seat_id:
                    return seat["status"]
    raise AssertionError(f"{seat_id} not on the map")


def ticket_type_for(client: TestClient, event_id: str, category: int) -> str:
    categories = seat_map(client, event_id)["categories"]
    return next(c["ticket_type_id"] for c in categories if c["category"] == category)


def buy_seats(
    client: TestClient,
    headers: dict[str, str],
    event_id: str,
    seats: list[str],
    category: int = 1,
) -> Response:
    return client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "event_id": event_id,
            "customer_name": "Arman Bekov",
            "customer_email": "arman@example.kz",
            "items": [
                {
                    "ticket_type_id": ticket_type_for(client, event_id, category),
                    "quantity": len(seats),
                    "seats": seats,
                }
            ],
        },
    )


def pay(client: TestClient, headers: dict[str, str], order_id: str) -> None:
    res = client.post(
        "/api/v1/payments/simulate",
        headers=headers,
        json={"order_id": order_id, "simulate_failure": False},
    )
    assert res.status_code in (200, 201), res.text


def pdf_text(pdf: bytes) -> bytes:
    """Decodes reportlab's ASCII85 + Flate content streams so the text can be searched."""
    streams = re.findall(rb"stream\r?\n(.*?)endstream", pdf, re.S)
    decoded = []
    for raw in streams:
        try:
            decoded.append(zlib.decompress(base64.a85decode(raw.strip(), adobe=True)))
        except (ValueError, zlib.error):
            continue
    return b"\n".join(decoded)


def test_main_hall_layout_matches_the_hall_plan() -> None:
    assert MAIN_HALL.seat_count() == 1000
    assert [MAIN_HALL.seat_count(c) for c in (1, 2, 3)] == [362, 363, 275]
    assert {s.id for s in MAIN_HALL.seats.values() if s.accessible} == {
        "D-A-24",
        "D-A-25",
        "F-A-7",
        "F-A-8",
    }


def test_setup_creates_one_ticket_type_per_category(
    client: TestClient, organizer_headers: dict[str, str], seated_event_id: str
) -> None:
    event = client.get(f"/api/v1/events/detail?event_id={seated_event_id}").json()
    categories = seat_map(client, seated_event_id)["categories"]

    assert event["is_assigned_seating"] is True
    assert event["capacity"] == 1000
    assert [(c["seat_count"], c["price"]) for c in categories] == [
        (362, PRICES[1]),
        (363, PRICES[2]),
        (275, PRICES[3]),
    ]

    # Running it again reprices instead of adding more ticket types.
    client.post(
        f"/api/v1/seating/setup?event_id={seated_event_id}",
        headers=organizer_headers,
        json={"categories": [{"category": 3, "name": "Balcony", "price": 300_000}]},
    )
    types = client.get(f"/api/v1/ticket-types?event_id={seated_event_id}").json()
    assert len(types) == 3
    balcony = next(t for t in types if t["seat_category"] == 3)
    assert (balcony["name"], balcony["price"], balcony["quantity"]) == ("Balcony", 300_000, 275)


def test_seat_is_held_during_checkout_then_sold_and_printed_on_the_ticket(
    client: TestClient, attendee_headers: dict[str, str], seated_event_id: str
) -> None:
    assert seat_status(client, seated_event_id, "E-A-15") == "available"

    order = buy_seats(client, attendee_headers, seated_event_id, ["E-A-15", "E-A-16"])
    assert order.status_code == 201, order.text
    assert order.json()["items"][0]["seats"] == ["E-A-15", "E-A-16"]
    assert order.json()["total_amount_kzt"] == 2 * PRICES[1]
    assert seat_status(client, seated_event_id, "E-A-15") == "held"

    pay(client, attendee_headers, order.json()["id"])
    assert seat_status(client, seated_event_id, "E-A-15") == "sold"

    tickets = client.get(
        f"/api/v1/tickets?order_id={order.json()['id']}", headers=attendee_headers
    ).json()
    assert sorted((t["section"], t["row"], t["seat"]) for t in tickets) == [
        ("E", "A", "15"),
        ("E", "A", "16"),
    ]
    pdf = client.get(f"/api/v1/tickets/pdf?ticket_id={tickets[0]['id']}", headers=attendee_headers)
    assert pdf.status_code == 200
    text = pdf_text(pdf.content)
    assert b"Section E \\267 Row A \\267 Seat 1" in text
    assert b"arman@example.kz" not in text  # no email on paper (SRS 4.7)


def test_two_orders_cannot_take_the_same_seat(
    client: TestClient,
    attendee_headers: dict[str, str],
    seated_event_id: str,
    organizer_headers: dict[str, str],
) -> None:
    first = buy_seats(client, attendee_headers, seated_event_id, ["E-B-12"])
    assert first.status_code == 201

    second = buy_seats(client, organizer_headers, seated_event_id, ["E-B-11", "E-B-12"])
    assert second.status_code == 409

    # The rejected order holds nothing: its other seat stays free.
    assert seat_status(client, seated_event_id, "E-B-11") == "available"
    types = client.get(f"/api/v1/ticket-types?event_id={seated_event_id}").json()
    assert next(t for t in types if t["seat_category"] == 1)["reserved_count"] == 1


def test_expired_hold_releases_the_seat(
    client: TestClient, attendee_headers: dict[str, str], seated_event_id: str
) -> None:
    abandoned = buy_seats(client, attendee_headers, seated_event_id, ["BC-J-20"], category=3)
    age_order(abandoned.json()["id"], settings.ORDER_HOLD_MINUTES + 1)

    assert seat_status(client, seated_event_id, "BC-J-20") == "available"
    again = buy_seats(client, attendee_headers, seated_event_id, ["BC-J-20"], category=3)
    assert again.status_code == 201


def test_refund_returns_the_seat_to_sale(
    client: TestClient,
    attendee_headers: dict[str, str],
    organizer_headers: dict[str, str],
    seated_event_id: str,
) -> None:
    order = buy_seats(client, attendee_headers, seated_event_id, ["A-L-30"], category=2).json()
    pay(client, attendee_headers, order["id"])

    refund = client.post(f"/api/v1/orders/refund?order_id={order['id']}", headers=organizer_headers)
    assert refund.status_code == 200
    assert seat_status(client, seated_event_id, "A-L-30") == "available"


@pytest.mark.parametrize(
    ("seats", "quantity", "category"),
    [
        (["E-A-15"], 2, 1),  # fewer seats than tickets
        (["Z-A-1"], 1, 1),  # no such seat
        (["BL-P-20"], 1, 1),  # balcony seat sold as lower parterre
        (["E-A-15", "E-A-15"], 2, 1),  # same seat twice
        ([], 1, 1),  # no seat at all
    ],
)
def test_invalid_seat_selections_are_rejected(
    client: TestClient,
    attendee_headers: dict[str, str],
    seated_event_id: str,
    seats: list[str],
    quantity: int,
    category: int,
) -> None:
    res = client.post(
        "/api/v1/orders",
        headers=attendee_headers,
        json={
            "event_id": seated_event_id,
            "customer_name": "Arman Bekov",
            "customer_email": "arman@example.kz",
            "items": [
                {
                    "ticket_type_id": ticket_type_for(client, seated_event_id, category),
                    "quantity": quantity,
                    "seats": seats,
                }
            ],
        },
    )
    assert res.status_code == 400


def test_free_seated_event_issues_tickets_at_once(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    event_id = create_seated_event(client, organizer_headers, {1: 0, 2: 0, 3: 0})

    order = buy_seats(client, attendee_headers, event_id, ["D-A-24"])

    assert order.json()["status"] == "paid"
    assert seat_status(client, event_id, "D-A-24") == "sold"


def test_general_admission_events_take_no_seats(
    client: TestClient, attendee_headers: dict[str, str], paid_event_id: str
) -> None:
    ticket_type_id = client.get(f"/api/v1/ticket-types?event_id={paid_event_id}").json()[0]["id"]
    res = client.post(
        "/api/v1/orders",
        headers=attendee_headers,
        json={
            "event_id": paid_event_id,
            "customer_name": "Arman Bekov",
            "customer_email": "arman@example.kz",
            "items": [{"ticket_type_id": ticket_type_id, "quantity": 1, "seats": ["E-A-15"]}],
        },
    )
    assert res.status_code == 400
    assert client.get(f"/api/v1/seating/map?event_id={paid_event_id}").status_code == 404


def test_layout_must_be_known_and_setup_needs_one(
    client: TestClient, organizer_headers: dict[str, str], paid_event_id: str
) -> None:
    unknown = client.post(
        "/api/v1/venues",
        json={"name": "X", "address": "Y", "layout_key": "nope"},
        headers=organizer_headers,
    )
    assert unknown.status_code == 422

    no_layout = client.post(
        f"/api/v1/seating/setup?event_id={paid_event_id}",
        headers=organizer_headers,
        json={"categories": [{"category": 1, "name": "Stalls", "price": 0}]},
    )
    assert no_layout.status_code == 404


def test_only_the_organizer_sets_up_seating(
    client: TestClient,
    other_organizer_headers: dict[str, str],
    seated_event_id: str,
) -> None:
    res = client.post(
        f"/api/v1/seating/setup?event_id={seated_event_id}",
        headers=other_organizer_headers,
        json={"categories": [{"category": 1, "name": "Stalls", "price": 0}]},
    )
    assert res.status_code == 404
