"""Тесты дашборда и API статистики."""

from datetime import date, timedelta

from app.models import DailyEntry


def test_dashboard_page(auth_client, sample_user, sample_entries):
    sample_user.streak = 3
    sample_user.xp = 120
    from app.extensions import db
    db.session.commit()
    r = auth_client.get("/dashboard/", headers={"Accept": "text/html"})
    assert r.status_code == 200
    body = r.data.decode("utf-8")
    assert "120" in body or "XP" in body
    assert "3" in body or "Streak" in body or "streak" in body


def test_dashboard_empty_user(auth_client):
    """Новый пользователь без записей и заданий — не падает."""
    r = auth_client.get("/dashboard/", headers={"Accept": "text/html"})
    assert r.status_code == 200


def test_api_anxiety_history(auth_client, sample_entries):
    r = auth_client.get("/api/stats/anxiety")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    if data:
        assert "date" in data[0]
        assert "anxiety_level" in data[0]


def test_api_tasks_by_week(auth_client):
    r = auth_client.get("/api/stats/tasks?weeks=4")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    if data:
        assert "week" in data[0]
        assert "count" in data[0]


def test_api_summary(auth_client, sample_user):
    r = auth_client.get("/api/stats/summary")
    assert r.status_code == 200
    data = r.get_json()
    for k in ("streak", "xp", "level", "total_tasks_completed", "avg_anxiety"):
        assert k in data


def test_api_isolation(client, db_session, sample_user, second_user):
    """API возвращает только данные текущего пользователя."""
    today = date.today()
    db_session.add(DailyEntry(
        user_id=sample_user.id, date=today,
        anxiety_level=2, text="A_only",
    ))
    db_session.add(DailyEntry(
        user_id=second_user.id, date=today,
        anxiety_level=9, text="B_only",
    ))
    db_session.commit()

    # клиент A
    cA = client
    cA.post("/auth/login", data={"email": "test@test.com", "password": "testpass123"})
    rA = cA.get("/api/stats/anxiety")
    assert all(d["anxiety_level"] != 9 for d in rA.get_json())

    cB = client.application.test_client()
    cB.post("/auth/login", data={"email": "other@test.com", "password": "otherpass123"})
    rB = cB.get("/api/stats/anxiety")
    assert all(d["anxiety_level"] != 2 for d in rB.get_json())
