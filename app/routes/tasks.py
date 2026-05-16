from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_babel import lazy_gettext as _
import sqlalchemy as sa

from app.extensions import db
from app.models import Task, UserTask
from app.services.task_service import TaskService

tasks_bp = Blueprint("tasks", __name__, template_folder="../templates/tasks")


@tasks_bp.get("/daily")
@jwt_required()
def daily():
    user_id = int(get_jwt_identity())
    anxiety_level = TaskService.get_last_anxiety_level(user_id)
    task = TaskService.get_daily_task(user_id, anxiety_level)

    # Check if already completed today
    today_completed = False
    if task:
        ut = db.session.execute(
            sa.select(UserTask).where(
                UserTask.user_id == user_id,
                UserTask.task_id == task.id,
                UserTask.completed == True,
            )
        ).scalar_one_or_none()
        if ut and ut.completed_at and ut.completed_at.date() == date.today():
            today_completed = True

    return render_template(
        "daily.html",
        task=task,
        anxiety_level=anxiety_level,
        today_completed=today_completed,
    )


@tasks_bp.post("/<int:task_id>/complete")
@jwt_required()
def complete(task_id: int):
    user_id = int(get_jwt_identity())
    feedback = request.form.get("feedback", "").strip()

    # Verify task exists
    task = db.session.execute(
        sa.select(Task).where(Task.id == task_id)
    ).scalar_one_or_none()
    if not task:
        abort(404)

    result = TaskService.complete_task(
        user_id, task_id, feedback if feedback else None
    )

    if result["xp_earned"] > 0:
        flash(f"{_('Task completed!')} +{result['xp_earned']} XP", "success")
        if result["leveled_up"]:
            flash(
                f"{_('New level! You reached level')} {result['new_level']}",
                "success",
            )
    else:
        flash(_("This task was already completed earlier"), "info")

    return render_template(
        "complete.html",
        task=task,
        result=result,
    )


@tasks_bp.get("/")
@jwt_required()
def index():
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1

    data = TaskService.get_user_task_history(user_id, page=page, per_page=10)
    completed_count = sum(1 for ut in data["tasks"] if ut.completed)
    total_xp_earned = sum(ut.task.xp_reward for ut in data["tasks"] if ut.completed)
    return render_template(
        "task_list.html",
        entries=data["tasks"],
        page=data["page"],
        total_pages=data["pages"],
        total=data["total"],
        completed_count=completed_count,
        total_xp_earned=total_xp_earned,
    )
