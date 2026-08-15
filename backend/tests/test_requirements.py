import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import cruds, schemas
from app.db import get_db
from app.main import app
from app.models import RefreshSession
from app.cruds import chat_crud


def user_payload(user_id: str, name: str) -> schemas.UserCreate:
    return schemas.UserCreate(id=user_id, username=name, password="Pass123")


def test_credentials_must_be_six_or_more_alphanumeric():
    with pytest.raises(ValidationError):
        schemas.UserCreate(id="short", username="Alice", password="Pass123")
    with pytest.raises(ValidationError):
        schemas.UserCreate(id="alice!", username="Alice", password="Pass123")
    with pytest.raises(ValidationError):
        schemas.UserCreate(id="alice01", username="Alice", password="pass word")


def test_friend_request_requires_acceptance(db):
    alice = cruds.create_user(db, user_payload("alice01", "Alice"))
    bob = cruds.create_user(db, user_payload("bob0001", "Bob"))

    request = cruds.create_friend_request(db, alice.id, bob.id)
    assert cruds.request_status(db, alice.id, bob.id) == "requested"
    assert cruds.request_status(db, bob.id, alice.id) == "incoming"
    assert not cruds.are_friends(db, alice.id, bob.id)

    cruds.accept_friend_request(db, request, bob.id)
    assert cruds.are_friends(db, alice.id, bob.id)
    assert cruds.are_friends(db, bob.id, alice.id)


def test_only_friends_can_read_and_readers_are_recorded(db):
    alice = cruds.create_user(db, user_payload("alice01", "Alice"))
    bob = cruds.create_user(db, user_payload("bob0001", "Bob"))
    chat = cruds.create_chat(db, schemas.ChatCreate(content="おはよう"), alice.id)

    with pytest.raises(PermissionError):
        cruds.message_history(db, bob, alice)

    request = cruds.create_friend_request(db, bob.id, alice.id)
    cruds.accept_friend_request(db, request, alice.id)
    # 友だち成立前の投稿は見えない。
    assert cruds.message_history(db, bob, alice) == []

    chat = cruds.create_chat(db, schemas.ChatCreate(content="友だちになった後"), alice.id)
    assert cruds.message_history(db, bob, alice) == [chat]

    viewers = cruds.message_viewers(db, chat.id, alice.id)
    assert [(viewer["user_id"], viewer["username"]) for viewer in viewers] == [("bob0001", "Bob")]


def test_message_history_is_limited_to_the_last_week(db):
    alice = cruds.create_user(db, user_payload("alice01", "Alice"))
    recent = cruds.create_chat(db, schemas.ChatCreate(content="最近"), alice.id)
    old = cruds.create_chat(db, schemas.ChatCreate(content="8日前"), alice.id)
    old.created_at = chat_crud.utc_now() - timedelta(days=8)
    db.commit()

    assert cruds.message_history(db, alice, alice) == [recent]


def test_inbox_starts_with_own_history_then_unread_friend(db):
    alice = cruds.create_user(db, user_payload("alice01", "Alice"))
    bob = cruds.create_user(db, user_payload("bob0001", "Bob"))
    request = cruds.create_friend_request(db, alice.id, bob.id)
    cruds.accept_friend_request(db, request, bob.id)
    cruds.create_chat(db, schemas.ChatCreate(content="自分のチャット"), alice.id)
    cruds.create_chat(db, schemas.ChatCreate(content="新着です"), bob.id)

    rows = cruds.inbox(db, alice)
    assert rows[0]["user_id"] == "alice01"
    assert rows[1]["user_id"] == "bob0001"
    assert rows[1]["read_status"] is False
    assert rows[1]["latest_message"] == "新着です"
    assert rows[1]["latest_message_at"] is not None


def test_templates_can_be_reordered_and_deleted_by_owner(db):
    alice = cruds.create_user(db, user_payload("alice01", "Alice"))
    bob = cruds.create_user(db, user_payload("bob0001", "Bob"))
    first = cruds.create_template(db, schemas.TemplateCreate(content="おはよう"), alice.id)
    second = cruds.create_template(db, schemas.TemplateCreate(content="おやすみ"), alice.id)

    assert cruds.reorder_templates(db, [second.id, first.id], alice.id)
    assert [item.id for item in cruds.get_templates(db, alice.id)] == [second.id, first.id]
    assert not cruds.delete_template(db, first.id, bob.id)
    assert cruds.delete_template(db, first.id, alice.id)


def test_refresh_token_is_rotated_and_reuse_revokes_family(db):
    alice = cruds.create_user(db, user_payload("alice01", "Alice"))
    first_token, first_session = cruds.create_refresh_session(db, alice.id, 60)

    second_token, second_session = cruds.rotate_refresh_session(db, first_token, 60)
    assert second_token != first_token
    assert second_session.token_family == first_session.token_family
    assert db.get(RefreshSession, first_session.id).revoked_at is not None

    with pytest.raises(cruds.InvalidRefreshTokenError):
        cruds.rotate_refresh_session(db, first_token, 60)

    db.refresh(second_session)
    assert second_session.revoked_at is not None


def test_login_refresh_and_logout_cookie_flow(db):
    cruds.create_user(db, user_payload("alice01", "Alice"))

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            login_response = client.post("/login", json={"id": "alice01", "password": "Pass123"})
            assert login_response.status_code == 200
            assert login_response.json()["user"] == {"user_id": "alice01", "username": "Alice"}
            assert "HttpOnly" in login_response.headers["set-cookie"]
            first_cookie = client.cookies.get("refresh_token")

            refresh_response = client.post("/auth/refresh")
            assert refresh_response.status_code == 200
            assert client.cookies.get("refresh_token") != first_cookie

            logout_response = client.post("/auth/logout")
            assert logout_response.status_code == 204
            assert client.post("/auth/refresh").status_code == 401
    finally:
        app.dependency_overrides.clear()
