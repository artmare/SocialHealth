import random
from datetime import date

import sqlalchemy as sa
from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import DailyEntry, User, UserTask
from app.services.stats_service import StatsService
from app.services.task_service import TaskService

dashboard_bp = Blueprint("dashboard", __name__)

MOTIVATIONAL_PHRASES = [
    "Каждый маленький шаг — это победа",
    "Сегодня — лучший день, чтобы стать чуть смелее",
    "Тревога приходит и уходит, а ты остаёшься",
    "Дыши глубже. Ты справляешься лучше, чем думаешь",
    "Прогресс важнее совершенства",
]


@dashboard_bp.get("/")
@jwt_required()
def index():
    user_id = int(get_jwt_identity())

    user = db.session.execute(
        sa.select(User).where(User.id == user_id)
    ).scalar_one()

    stats = StatsService.get_dashboard_stats(user_id)
    comparison = StatsService.get_anxiety_comparison(user_id)

    anxiety_level = TaskService.get_last_anxiety_level(user_id)
    daily_task = TaskService.get_daily_task(user_id, anxiety_level)

    today_completed = False
    if daily_task:
        ut = db.session.execute(
            sa.select(UserTask).where(
                UserTask.user_id == user_id,
                UserTask.task_id == daily_task.id,
                UserTask.completed == True,
            )
        ).scalar_one_or_none()
        if ut and ut.completed_at and ut.completed_at.date() == date.today():
            today_completed = True

    last_entry = db.session.execute(
        sa.select(DailyEntry)
        .where(DailyEntry.user_id == user_id)
        .order_by(DailyEntry.date.desc(), DailyEntry.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    return render_template(
        "dashboard/index.html",
        user=user,
        display_name=user.username or user.email,
        today=date.today(),
        motivation=random.choice(MOTIVATIONAL_PHRASES),
        stats=stats,
        comparison=comparison,
        daily_task=daily_task,
        today_completed=today_completed,
        last_entry=last_entry,
    )
