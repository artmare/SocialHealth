"""Тесты CBT-заданий."""

import re
from datetime import date, timedelta

import pytest
import sqlalchemy as sa

from app.extensions import db
from app.models import Achievement, Task, UserAchievement, UserTask, User
from app.services.task_service import TaskService


@pytest.mark.parametrize("level,expected", [
    (1, "easy"), (2, "easy"), (3, "easy"),
    (4, "medium"), (5, "medium"), (6, "medium"),
    (7, "hard"), (8, "hard"), (9, "hard"), (10, "hard"),
])
def test_get_difficulty_for_anxiety(level, expected):
    assert TaskService.get_difficulty_for_anxiety(level) == expected


def test_get_daily_task_easy(db_session, sample_user, sample_tasks):
    task = TaskService.get_daily_task(sample_user.id, anxiety_level=2)
    assert task is not None
    assert task.difficulty == "easy"


def test_get_daily_task_medium(db_session, sample_user, sample_tasks):
    task = TaskService.get_daily_task(sample_user.id, anxiety_level=5)
    assert task is not None
    assert task.difficulty == "medium"


def test_get_daily_task_hard(db_session, sample_user, sample_tasks):
    task = TaskService.get_daily_task(sample_user.id, anxiety_level=8)
    assert task is not None
    assert task.difficulty == "hard"


def test_get_daily_task_excludes_completed(db_session, sample_user, sample_tasks):
    # выполним все easy кроме одного
    easy_tasks = [t for t in sample_tasks if t.difficulty == "easy"]
    for t in easy_tasks[:-1]:
        TaskService.complete_task(sample_user.id, t.id)
    last_id = easy_tasks[-1].id
    # должны получить именно невыполненный
    next_task = TaskService.get_daily_task(sample_user.id, 2)
    assert next_task is not None
    assert next_task.id == last_id


def test_get_daily_task_cycle_reset(db_session, sample_user, sample_tasks):
    """Все easy выполнены → возвращается какой-то easy (не None) — цикл."""
    for t in [t for t in sample_tasks if t.difficulty == "easy"]:
        TaskService.complete_task(sample_user.id, t.id)
    nxt = TaskService.get_daily_task(sample_user.id, 2)
    assert nxt is not None
    assert nxt.difficulty == "easy"


def test_complete_task_xp(db_session, sample_user, sample_tasks):
    easy = next(t for t in sample_tasks if t.difficulty == "easy")
    result = TaskService.complete_task(sample_user.id, easy.id)
    assert result["xp_earned"] == 10
    db_session.refresh(sample_user)
    assert sample_user.xp == 10


def test_complete_task_levelup(db_session, sample_user, sample_tasks):
    sample_user.xp = 90; db_session.commit()
    easy = next(t for t in sample_tasks if t.difficulty == "easy")
    result = TaskService.complete_task(sample_user.id, easy.id)
    assert result["leveled_up"] is True
    assert result["new_level"] == 2


def test_complete_task_streak_new(db_session, sample_user, sample_tasks):
    easy = next(t for t in sample_tasks if t.difficulty == "easy")
    result = TaskService.complete_task(sample_user.id, easy.id)
    assert result["streak"] == 1
    db_session.refresh(sample_user)
    assert sample_user.streak == 1
    assert sample_user.last_activity_date == date.today()


def test_complete_task_streak_continue(db_session, sample_user, sample_tasks):
    sample_user.streak = 3
    sample_user.last_activity_date = date.today() - timedelta(days=1)
    db_session.commit()
    easy = next(t for t in sample_tasks if t.difficulty == "easy")
    TaskService.complete_task(sample_user.id, easy.id)
    db_session.refresh(sample_user)
    assert sample_user.streak == 4


def test_complete_task_streak_reset(db_session, sample_user, sample_tasks):
    sample_user.streak = 5
    sample_user.last_activity_date = date.today() - timedelta(days=3)
    db_session.commit()
    easy = next(t for t in sample_tasks if t.difficulty == "easy")
    TaskService.complete_task(sample_user.id, easy.id)
    db_session.refresh(sample_user)
    assert sample_user.streak == 1


def test_seed_tasks_count(db_session, sample_tasks):
    total = db_session.scalar(sa.select(sa.func.count(Task.id)))
    easy = db_session.scalar(
        sa.select(sa.func.count(Task.id)).where(Task.difficulty == "easy")
    )
    medium = db_session.scalar(
        sa.select(sa.func.count(Task.id)).where(Task.difficulty == "medium")
    )
    hard = db_session.scalar(
        sa.select(sa.func.count(Task.id)).where(Task.difficulty == "hard")
    )
    assert total == 30
    assert easy == 10
    assert medium == 10
    assert hard == 10


def test_daily_task_completion_uses_post_form(auth_client, sample_tasks):
    response = auth_client.get("/tasks/daily", headers={"Accept": "text/html"})

    assert response.status_code == 200
    body = response.data.decode("utf-8")
    assert 'method="post"' in body
    assert "/tasks/" in body and "/complete" in body
    assert not re.search(r'<a\s+href="/tasks/\d+/complete"', body)


def test_daily_task_can_be_completed_by_post(
    auth_client, db_session, sample_user, sample_tasks
):
    task = next(t for t in sample_tasks if t.difficulty == "easy")

    response = auth_client.post(
        f"/tasks/{task.id}/complete",
        data={"feedback": "done"},
        headers={"Accept": "text/html"},
    )

    assert response.status_code == 200
    user_task = db_session.execute(
        sa.select(UserTask).where(
            UserTask.user_id == sample_user.id,
            UserTask.task_id == task.id,
            UserTask.completed == True,
        )
    ).scalar_one()
    assert user_task.feedback == "done"


def test_task_completion_awards_achievements(db_session, sample_user, sample_tasks):
    task = next(t for t in sample_tasks if t.difficulty == "easy")

    TaskService.complete_task(sample_user.id, task.id)

    achievements = db_session.execute(
        sa.select(Achievement.name)
        .join(UserAchievement)
        .where(UserAchievement.user_id == sample_user.id)
    ).scalars().all()
    assert "First step" in achievements
