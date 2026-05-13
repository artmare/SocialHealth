"""Тесты профиля и настроек."""

import json

import sqlalchemy as sa

from app.extensions import db
from app.models import User, UserSettings, DailyEntry


def test_profile_page(auth_client, sample_user):
    r = auth_client.get("/profile/", headers={"Accept": "text/html"})
    assert r.status_code == 200
    body = r.data.decode("utf-8")
    assert sample_user.email in body or sample_user.username in body


def test_change_password_success(auth_client, sample_user):
    r = auth_client.post("/profile/change-password", data={
        "current_password": "testpass123",
        "new_password": "brandnew123",
        "confirm_password": "brandnew123",
    }, follow_redirects=False)
    assert r.status_code in (301, 302, 303, 307, 308)
    db.session.refresh(sample_user)
    assert sample_user.check_password("brandnew123") is True
    assert sample_user.check_password("testpass123") is False


def test_change_password_wrong_current(auth_client, sample_user):
    r = auth_client.post("/profile/change-password", data={
        "current_password": "WRONG",
        "new_password": "brandnew123",
        "confirm_password": "brandnew123",
    }, follow_redirects=False)
    assert r.status_code not in (301, 302, 303, 307, 308)
    db.session.refresh(sample_user)
    assert sample_user.check_password("testpass123") is True


def test_change_password_short(auth_client, sample_user):
    r = auth_client.post("/profile/change-password", data={
        "current_password": "testpass123",
        "new_password": "short",
        "confirm_password": "short",
    }, follow_redirects=False)
    assert r.status_code not in (301, 302, 303, 307, 308)
    db.session.refresh(sample_user)
    assert sample_user.check_password("testpass123") is True


def test_settings_update(auth_client, sample_user):
    auth_client.post("/profile/settings", data={
        "dark_mode": "on",
        "language": "en",
        "daily_reminder_time": "21:30",
    }, follow_redirects=False)
    s = db.session.execute(
        sa.select(UserSettings).where(UserSettings.user_id == sample_user.id)
    ).scalar_one()
    assert s.dark_mode is True
    assert s.notifications_enabled is False  # checkbox не отправлен
    assert s.language == "en"
    assert s.daily_reminder_time == "21:30"


def test_export_json(auth_client, sample_user, sample_entries):
    r = auth_client.post("/profile/export", data={"format": "json"})
    assert r.status_code == 200
    payload = json.loads(r.data.decode("utf-8"))
    assert "entries" in payload
    assert "tasks" in payload
    assert payload["user"]["email"] == sample_user.email


def test_delete_account(client, db_session, sample_user, sample_entries):
    uid = sample_user.id
    client.post("/auth/login", data={
        "email": "test@test.com", "password": "testpass123",
    })
    r = client.post("/profile/delete-account", data={
        "password": "testpass123",
        "confirmation": "УДАЛИТЬ",
    }, follow_redirects=False)
    assert r.status_code in (301, 302, 303, 307, 308)

    assert db_session.get(User, uid) is None
    rest = db_session.execute(
        sa.select(DailyEntry).where(DailyEntry.user_id == uid)
    ).scalars().all()
    assert rest == []


def test_delete_account_no_confirm(auth_client, sample_user):
    r = auth_client.post("/profile/delete-account", data={
        "password": "testpass123",
    }, follow_redirects=False)
    assert r.status_code not in (301, 302, 303, 307, 308)
    # Аккаунт не удалён
    assert db.session.get(User, sample_user.id) is not None
