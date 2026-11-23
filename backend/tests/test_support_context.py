from conftest import create_paid_event, make_headers, place_order
from fastapi.testclient import TestClient


def bought_ticket(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> tuple[str, dict, dict]:
    event_id = create_paid_event(client, organizer_headers, price=0)
    order = place_order(client, attendee_headers, event_id).json()
    ticket = client.get(f"/api/v1/tickets?order_id={order['id']}", headers=attendee_headers).json()[
        0
    ]
    return event_id, order, ticket


def open_case(client: TestClient, headers: dict[str, str], **context: str):
    return client.post(
        "/api/v1/support/cases",
        headers=headers,
        json={
            "target": "organizer",
            "category": "ticket_delivery",
            "subject": "QR does not scan",
            "message": "The scanner rejects my ticket.",
            **context,
        },
    )


def test_case_from_a_ticket_carries_order_and_event(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    event_id, order, ticket = bought_ticket(client, organizer_headers, attendee_headers)

    res = open_case(client, attendee_headers, ticket_id=ticket["id"])

    assert res.status_code == 201
    case = res.json()
    assert case["event_id"] == event_id
    assert case["order_id"] == order["id"]
    assert case["ticket_id"] == ticket["id"]
    assert case["ticket_type_name"] == "Standard"
    assert case["ticket_status"] == "valid"
    assert case["order_status"] == "paid"

    # The organizer handling the case sees the same context.
    seen = client.get(
        f"/api/v1/support/cases/detail?case_id={case['id']}", headers=organizer_headers
    )
    assert seen.status_code == 200
    assert seen.json()["ticket_id"] == ticket["id"]


def test_case_from_an_order_fills_in_the_event(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    event_id, order, _ = bought_ticket(client, organizer_headers, attendee_headers)

    res = open_case(client, attendee_headers, order_id=order["id"])

    assert res.status_code == 201
    assert res.json()["event_id"] == event_id
    assert res.json()["ticket_id"] is None


def test_someone_elses_ticket_cannot_be_attached(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    _, _, ticket = bought_ticket(client, organizer_headers, attendee_headers)
    stranger = make_headers(client, "stranger@example.com", "attendee")

    assert open_case(client, stranger, ticket_id=ticket["id"]).status_code == 404


def test_context_must_match_the_event(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    _, order, _ = bought_ticket(client, organizer_headers, attendee_headers)
    other_event = create_paid_event(client, organizer_headers, price=0)

    res = open_case(client, attendee_headers, order_id=order["id"], event_id=other_event)

    assert res.status_code == 400
