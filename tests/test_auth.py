"""Тесты авторизации."""

import sqlalchemy as sa

from app.models import User


def test_register_success(client, db_session):
    r = client.post("/auth/register", data={
        "username": "newuser",
        "email": "new@test.com",
        "password": "newpass1234",
        "confirm_password": "newpass1234",
    }, follow_redirects=False)
    assert r.status_code in (200, 201, 301, 302, 303, 307, 308)
    u = db_session.execute(
        sa.select(User).where(User.email == "new@test.com")
    ).scalar_one_or_none()
    assert u is not None


def test_register_duplicate_email(client, sample_user):
    r = client.post("/auth/register", data={
        "username": "dup",
        "email": "test@test.com",  # уже занят sample_user
        "password": "newpass1234",
        "confirm_password": "newpass1234",
    })
    body = r.data.decode("utf-8")
    assert "уже существует" in body or r.status_code >= 400 or "error" in body.lower()


def test_register_short_password(client):
    r = client.post("/auth/register", data={
        "username": "shortp",
        "email": "short@test.com",
        "password": "abc",
        "confirm_password": "abc",
    })
    body = r.data.decode("utf-8")
    # форма должна вернуть ту же страницу с ошибкой (не редирект)
    assert r.status_code not in (301, 302, 303, 307, 308) or "ошибк" in body.lower()


def test_register_missing_email(client):
    r = client.post("/auth/register", data={
        "username": "noemail",
        "password": "newpass1234",
        "confirm_password": "newpass1234",
    })
    assert r.status_code not in (301, 302, 303, 307, 308)


def test_login_success(client, sample_user):
    r = client.post("/auth/login", data={
        "email": "test@test.com",
        "password": "testpass123",
    }, follow_redirects=False)
    assert r.status_code in (301, 302, 303, 307, 308)
    cookies = r.headers.getlist("Set-Cookie")
    assert any("access_token_cookie" in c for c in cookies)
    assert any("refresh_token_cookie" in c for c in cookies)


def test_login_wrong_password(client, sample_user):
    r = client.post("/auth/login", data={
        "email": "test@test.com",
        "password": "wrongpass",
    }, follow_redirects=False)
    # Login возвращает форму с ошибкой (200), не редирект
    assert r.status_code not in (301, 302, 303, 307, 308)


def test_login_nonexistent_user(client):
    r = client.post("/auth/login", data={
        "email": "ghost@test.com",
        "password": "anypass1234",
    }, follow_redirects=False)
    assert r.status_code not in (301, 302, 303, 307, 308)


def test_protected_route_without_token(client):
    r = client.get("/dashboard/", follow_redirects=False)
    # либо 401 (API), либо редирект на /auth/login (HTML с Accept: text/html)
    assert r.status_code in (401, 301, 302, 303, 307, 308)


def test_protected_route_with_token(auth_client):
    r = auth_client.get("/dashboard/", headers={"Accept": "text/html"})
    assert r.status_code == 200


def test_refresh_token(client, sample_user):
    client.post("/auth/login", data={
        "email": "test@test.com",
        "password": "testpass123",
    })
    r = client.post("/auth/refresh")
    assert r.status_code == 200
    data = r.get_json()
    assert "access_token" in data
