from fastapi.testclient import TestClient

USER = {"email": "ann@example.com", "password": "s3cretpass", "full_name": "Ann"}


def login(client: TestClient) -> str:
    client.post("/api/v1/auth/register", json=USER)
    response = client.post(
        "/api/v1/auth/login", json={"email": USER["email"], "password": USER["password"]}
    )
    return response.json()["access_token"]


def test_register_returns_user_without_password(client: TestClient) -> None:
    response = client.post("/api/v1/auth/register", json=USER)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == USER["email"]
    assert body["role"] == "attendee"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_email_conflicts(client: TestClient) -> None:
    client.post("/api/v1/auth/register", json=USER)

    response = client.post("/api/v1/auth/register", json=USER)

    assert response.status_code == 409


def test_login_wrong_password_unauthorized(client: TestClient) -> None:
    client.post("/api/v1/auth/register", json=USER)

    response = client.post(
        "/api/v1/auth/login", json={"email": USER["email"], "password": "wrong-password"}
    )

    assert response.status_code == 401


def test_me_with_token(client: TestClient) -> None:
    token = login(client)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == USER["email"]


def test_me_without_or_with_bad_token_unauthorized(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401

    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401
