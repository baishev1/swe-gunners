from collections.abc import Callable, Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import core
from app.main import app
from core import Session
from features.users.dependencies import get_current_user as get_support_user
from features.users.models import User


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        if core.engine is not None:
            core.DbBase.metadata.create_all(core.engine)
        yield test_client


@pytest.fixture
def login(client: TestClient) -> Iterator[Callable[[str], User]]:
    users: dict[str, User] = {}
    assert core.engine is not None
    with Session(core.engine) as db:
        for name, role in (
            ("attendee", "attendee"),
            ("other", "attendee"),
            ("organizer", "organizer"),
            ("other_organizer", "organizer"),
            ("admin", "platform_admin"),
        ):
            user = User(
                email=f"{uuid4()}@example.com",
                full_name=name,
                password_hash="unused-in-tests",
                role=role,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            db.expunge(user)
            users[name] = user

    def switch(name: str) -> User:
        user = users[name]
        app.dependency_overrides[get_support_user] = lambda: user
        return user

    switch("attendee")
    try:
        yield switch
    finally:
        app.dependency_overrides.pop(get_support_user, None)
