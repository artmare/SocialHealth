"""Тесты дневника эмоций."""

from datetime import date, timedelta
from unittest.mock import patch

import sqlalchemy as sa

from app.models import DailyEntry


@patch("app.routes.diary.AIService.analyze_entry")
def test_create_entry_success(mock_ai, auth_client, db_session, sample_user):
    mock_ai.return_value = {"summary": "ok", "insight": "x", "recommendation": "y"}
    r = auth_client.post("/diary/new", data={
        "anxiety_level": "5",
        "text": "сегодня тяжело",
        "emotions": ["страх"],
    }, follow_redirects=False)
    assert r.status_code in (301, 302, 303, 307, 308)
    entries = db_session.execute(
        sa.select(DailyEntry).where(DailyEntry.user_id == sample_user.id)
    ).scalars().all()
    assert len(entries) == 1
    assert entries[0].anxiety_level == 5


def test_create_entry_invalid_anxiety_low(auth_client):
    r = auth_client.post("/diary/new", data={
        "anxiety_level": "0",
        "text": "test",
    }, follow_redirects=False)
    assert r.status_code not in (301, 302, 303, 307, 308)


def test_create_entry_invalid_anxiety_high(auth_client):
    r = auth_client.post("/diary/new", data={
        "anxiety_level": "11",
        "text": "test",
    }, follow_redirects=False)
    assert r.status_code not in (301, 302, 303, 307, 308)


@patch("app.routes.diary.AIService.analyze_entry")
def test_create_entry_ai_analysis(mock_ai, auth_client, db_session, sample_user):
    mock_ai.return_value = {
        "summary": "Запись о тревоге",
        "insight": "катастрофизация",
        "recommendation": "техника 4-7-8",
    }
    auth_client.post("/diary/new", data={
        "anxiety_level": "6",
        "text": "выступление завтра",
    })
    e = db_session.execute(
        sa.select(DailyEntry).where(DailyEntry.user_id == sample_user.id)
    ).scalar_one()
    assert e.ai_analysis is not None
    assert e.ai_analysis["summary"] == "Запись о тревоге"


def test_list_entries(auth_client, sample_entries):
    r = auth_client.get("/diary/", headers={"Accept": "text/html"})
    assert r.status_code == 200
    body = r.data.decode("utf-8")
    assert "запись" in body.lower() or "Дневник" in body


def test_list_entries_pagination(auth_client, db_session, sample_user):
    today = date.today()
    for i in range(15):
        db_session.add(DailyEntry(
            user_id=sample_user.id, date=today - timedelta(days=i),
            anxiety_level=5, text=f"e{i}",
        ))
    db_session.commit()
    r1 = auth_client.get("/diary/?page=1", headers={"Accept": "text/html"})
    assert r1.status_code == 200
    r2 = auth_client.get("/diary/?page=2", headers={"Accept": "text/html"})
    assert r2.status_code == 200
    # На странице 2 должна быть пагинация
    body2 = r2.data.decode("utf-8")
    assert "page=" in body2 or "Страница" in body2 or "15" in body2


def test_entry_detail(auth_client, sample_entries):
    eid = sample_entries[0].id
    r = auth_client.get(f"/diary/{eid}", headers={"Accept": "text/html"})
    assert r.status_code == 200


def test_entry_detail_forbidden(client, db_session, sample_user, second_user):
    """Чужая запись → 404 (или 403)."""
    e = DailyEntry(
        user_id=second_user.id, date=date.today(),
        anxiety_level=5, text="other-private",
    )
    db_session.add(e); db_session.commit()
    eid = e.id

    client.post("/auth/login", data={
        "email": "test@test.com", "password": "testpass123",
    })
    r = client.get(f"/diary/{eid}", headers={"Accept": "text/html"})
    assert r.status_code in (403, 404)


def test_entry_isolation(client, db_session, sample_user, second_user):
    """Пользователь А не видит записи Б в /diary/."""
    db_session.add(DailyEntry(
        user_id=second_user.id, date=date.today(),
        anxiety_level=8, text="OTHER_PRIVATE_TEXT",
    ))
    db_session.commit()

    client.post("/auth/login", data={
        "email": "test@test.com", "password": "testpass123",
    })
    r = client.get("/diary/", headers={"Accept": "text/html"})
    assert "OTHER_PRIVATE_TEXT" not in r.data.decode("utf-8")
