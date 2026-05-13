"""Общие фикстуры pytest для проекта SocialHealth."""

from datetime import date, datetime, timedelta, timezone

import pytest

from app import create_app
from app.extensions import db as _db
from app.models import (
    User,
    UserSettings,
    DailyEntry,
    Task,
    UserTask,
    Achievement,
)


# ============================================================
# core
# ============================================================

@pytest.fixture
def app():
    """Создать Flask-app с TestingConfig (SQLite in-memory) и схемой БД."""
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Flask test-client для HTTP-запросов."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Сессия БД для прямой работы с моделями."""
    return _db.session


# ============================================================
# users
# ============================================================

@pytest.fixture
def sample_user(db_session):
    """Тестовый пользователь test@test.com / testpass123 + UserSettings c дефолтами."""
    user = User(username="testuser", email="test@test.com")
    user.set_password("testpass123")
    db_session.add(user)
    db_session.commit()
    settings = UserSettings(user_id=user.id)
    db_session.add(settings)
    db_session.commit()
    return user


@pytest.fixture
def second_user(db_session):
    """Второй пользователь для тестов изоляции."""
    user = User(username="otheruser", email="other@test.com")
    user.set_password("otherpass123")
    db_session.add(user)
    db_session.commit()
    settings = UserSettings(user_id=user.id)
    db_session.add(settings)
    db_session.commit()
    return user


@pytest.fixture
def auth_headers(client, sample_user):
    """JWT access_token в виде заголовка Authorization для авторизованных запросов."""
    from flask_jwt_extended import create_access_token
    with client.application.app_context():
        token = create_access_token(identity=str(sample_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_client(client, sample_user):
    """Test-client уже залогиненный через POST /auth/login (cookies)."""
    client.post(
        "/auth/login",
        data={"email": "test@test.com", "password": "testpass123"},
        follow_redirects=False,
    )
    return client


# ============================================================
# data fixtures
# ============================================================

@pytest.fixture
def sample_entries(db_session, sample_user):
    """5 DailyEntry с разными anxiety_level и датами."""
    today = date.today()
    levels = [3, 5, 7, 4, 6]
    entries = []
    for i, lvl in enumerate(levels):
        e = DailyEntry(
            user_id=sample_user.id,
            date=today - timedelta(days=i),
            anxiety_level=lvl,
            text=f"запись {i}",
        )
        db_session.add(e)
        entries.append(e)
    db_session.commit()
    return entries


@pytest.fixture
def sample_tasks(db_session):
    """30 заданий: 10 easy / 10 medium / 10 hard (через seed_tasks.py)."""
    import importlib.util
    import os
    spec = importlib.util.spec_from_file_location(
        "seed_tasks", os.path.join(os.path.dirname(__file__), "..", "seed_tasks.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # seed принимает app — используем текущий
    from flask import current_app
    module.seed(current_app)
    return Task.query.all()


@pytest.fixture
def completed_task(db_session, sample_user, sample_tasks):
    """Один UserTask, выполненный, с начисленным XP."""
    from app.services.task_service import TaskService
    task = next(t for t in sample_tasks if t.difficulty == "easy")
    TaskService.complete_task(sample_user.id, task.id)
    return db_session.query(UserTask).filter_by(
        user_id=sample_user.id, task_id=task.id
    ).first()
