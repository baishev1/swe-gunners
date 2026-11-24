from urllib.parse import parse_qs, urlsplit

from conftest import create_paid_event
from fastapi.testclient import TestClient


def make_event(client: TestClient, headers: dict[str, str], visibility: str) -> str:
    event_id = create_paid_event(client, headers, price=0)
    res = client.patch(
        f"/api/v1/events/update?event_id={event_id}",
        json={"visibility": visibility},
        headers=headers,
    )
    assert res.status_code == 200
    return event_id


def access_token(client: TestClient, headers: dict[str, str], event_id: str) -> str:
    res = client.get(f"/api/v1/events/access-link?event_id={event_id}", headers=headers)
    assert res.status_code == 200
    query = parse_qs(urlsplit(res.json()["link"]).query)
    assert query["event_id"] == [event_id]
    return query["access"][0]


def order(client: TestClient, headers: dict[str, str], event_id: str, access: str | None):
    ticket_types = client.get(f"/api/v1/ticket-types?event_id={event_id}&access={access or ''}")
    ticket_type_id = ticket_types.json()[0]["id"] if ticket_types.status_code == 200 else None
    return client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "event_id": event_id,
            "customer_name": "Arman Bekov",
            "customer_email": "arman@example.kz",
            "items": [{"ticket_type_id": ticket_type_id or event_id, "quantity": 1}],
            "access_token": access,
        },
    )


def test_private_event_opens_only_with_its_secret_link(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    event_id = make_event(client, organizer_headers, "private")
    token = access_token(client, organizer_headers, event_id)

    assert client.get(f"/api/v1/events/detail?event_id={event_id}").status_code == 404
    wrong = client.get(f"/api/v1/events/detail?event_id={event_id}&access=guess")
    assert wrong.status_code == 404
    assert client.get(f"/api/v1/ticket-types?event_id={event_id}").status_code == 404
    assert event_id not in [e["id"] for e in client.get("/api/v1/events").json()]

    detail = client.get(f"/api/v1/events/detail?event_id={event_id}&access={token}")
    assert detail.status_code == 200
    assert "access_token" not in detail.json()


def test_private_event_sells_only_through_the_link(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    event_id = make_event(client, organizer_headers, "private")
    token = access_token(client, organizer_headers, event_id)

    # Knowing the event ID is not enough to buy.
    assert order(client, attendee_headers, event_id, None).status_code == 404

    placed = order(client, attendee_headers, event_id, token)
    assert placed.status_code == 201

    # Ticket holders keep seeing the event (tickets, support) without the link.
    holder_view = client.get(f"/api/v1/events/detail?event_id={event_id}", headers=attendee_headers)
    assert holder_view.status_code == 200
    case = client.post(
        "/api/v1/support/cases",
        headers=attendee_headers,
        json={
            "target": "organizer",
            "event_id": event_id,
            "category": "ticket_delivery",
            "subject": "Where is my ticket?",
            "message": "Please check.",
        },
    )
    assert case.status_code == 201


def test_unlisted_event_is_hidden_from_the_list_but_open_by_link(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    event_id = make_event(client, organizer_headers, "unlisted")

    assert event_id not in [e["id"] for e in client.get("/api/v1/events").json()]
    assert client.get(f"/api/v1/events/detail?event_id={event_id}").status_code == 200
    assert order(client, attendee_headers, event_id, None).status_code == 201


def test_only_the_organizer_reads_the_access_link(
    client: TestClient,
    organizer_headers: dict[str, str],
    other_organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
) -> None:
    event_id = make_event(client, organizer_headers, "private")
    url = f"/api/v1/events/access-link?event_id={event_id}"

    assert client.get(url, headers=other_organizer_headers).status_code == 404
    assert client.get(url, headers=attendee_headers).status_code in (403, 404)
