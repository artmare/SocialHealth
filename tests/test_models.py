"""Тесты моделей БД."""

from datetime import date, datetime, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import (
    User,
    UserSettings,
    DailyEntry,
    Task,
    UserTask,
    Achievement,
    UserAchievement,
)


def test_user_creation(db_session):
    u = User(username="u1", email="u1@test.com")
    u.set_password("pass1234")
    db_session.add(u); db_session.commit()
    assert u.id is not None
    assert u.xp == 0
    assert u.level == 1
    assert u.streak == 0
    assert u.longest_streak == 0


def test_user_password_hashing(db_session):
    u = User(username="u2", email="u2@test.com")
    u.set_password("supersecret123")
    assert u.password_hash != "supersecret123"
    assert u.check_password("supersecret123") is True
    assert u.check_password("wrong") is False


def test_user_add_xp_no_levelup(db_session):
    u = User(username="u3", email="u3@test.com")
    u.set_password("p"); db_session.add(u); db_session.commit()
    leveled = u.add_xp(50)
    assert u.xp == 50
    assert u.level == 1
    assert leveled is False


def test_user_add_xp_levelup(db_session):
    u = User(username="u4", email="u4@test.com")
    u.set_password("p"); db_session.add(u); db_session.commit()
    leveled = u.add_xp(100)
    assert u.xp == 100
    assert u.level == 2
    assert leveled is True


def test_user_max_level(db_session):
    u = User(username="u5", email="u5@test.com")
    u.set_password("p"); db_session.add(u); db_session.commit()
    u.add_xp(5000)
    assert u.level == 10
    # Дальнейший XP не ломает
    u.add_xp(10000)
    assert u.level == 10
    assert u.xp == 15000


def test_daily_entry_creation(db_session):
    u = User(username="ude", email="ude@test.com"); u.set_password("p")
    db_session.add(u); db_session.commit()
    e = DailyEntry(
        user_id=u.id, date=date.today(),
        anxiety_level=7, emotions=["тревога", "страх"],
        text="сегодня тяжело",
    )
    db_session.add(e); db_session.commit()
    assert e.id is not None
    assert e.anxiety_level == 7
    assert e.emotions == ["тревога", "страх"]


def test_task_creation(db_session):
    t = Task(title="Дыхание", description="d",
             difficulty="easy", xp_reward=10, category="breathing")
    db_session.add(t); db_session.commit()
    assert t.id is not None
    assert t.difficulty == "easy"
    assert t.xp_reward == 10


def test_user_task_completion(db_session):
    u = User(username="utc", email="utc@test.com"); u.set_password("p")
    t = Task(title="T", description="d",
             difficulty="easy", xp_reward=10, category="breathing")
    db_session.add_all([u, t]); db_session.commit()
    ut = UserTask(user_id=u.id, task_id=t.id, completed=False)
    db_session.add(ut); db_session.commit()
    assert ut.completed is False
    ut.completed = True
    ut.completed_at = datetime.now(timezone.utc)
    db_session.commit()
    assert ut.completed is True
    assert ut.completed_at is not None


def test_achievement_creation(db_session):
    a = Achievement(
        name="Первый шаг", description="d", icon="🥇",
        condition_type="tasks_completed", condition_value=1,
    )
    db_session.add(a); db_session.commit()
    assert a.id is not None
    assert a.condition_type == "tasks_completed"
    assert a.condition_value == 1


def test_user_achievement_unique_constraint(db_session):
    u = User(username="ua", email="ua@test.com"); u.set_password("p")
    a = Achievement(name="A", description="d", icon="x",
                    condition_type="streak", condition_value=1)
    db_session.add_all([u, a]); db_session.commit()

    db_session.add(UserAchievement(user_id=u.id, achievement_id=a.id))
    db_session.commit()
    with pytest.raises(IntegrityError):
        db_session.add(UserAchievement(user_id=u.id, achievement_id=a.id))
        db_session.commit()
    db_session.rollback()


def test_user_settings_defaults(db_session):
    u = User(username="us", email="us@test.com"); u.set_password("p")
    db_session.add(u); db_session.commit()
    s = UserSettings(user_id=u.id)
    db_session.add(s); db_session.commit()
    assert s.dark_mode is False
    assert s.notifications_enabled is True
    assert s.language == "ru"


def test_user_entries_relationship(db_session, sample_user, sample_entries):
    u = db_session.execute(
        sa.select(User).where(User.id == sample_user.id)
    ).scalar_one()
    assert len(u.entries) == 5


def test_user_tasks_relationship(db_session, sample_user):
    t = Task(title="T", description="d",
             difficulty="easy", xp_reward=10, category="breathing")
    db_session.add(t); db_session.commit()
    db_session.add(UserTask(user_id=sample_user.id, task_id=t.id, completed=False))
    db_session.commit()
    db_session.refresh(sample_user)
    assert len(sample_user.user_tasks) == 1


def test_cascade_delete_user(db_session, sample_user, sample_entries):
    """Удаление User → удаляются связанные DailyEntry/UserSettings (ON DELETE CASCADE)."""
    uid = sample_user.id
    db_session.delete(sample_user)
    db_session.commit()
    rest = db_session.execute(
        sa.select(DailyEntry).where(DailyEntry.user_id == uid)
    ).scalars().all()
    assert rest == []
