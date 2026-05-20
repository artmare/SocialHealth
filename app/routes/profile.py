import io
import json
from datetime import datetime, timezone

import sqlalchemy as sa
from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    make_response,
)
from flask_babel import lazy_gettext as _
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    unset_jwt_cookies,
)

from app.extensions import db
from app.models import (
    User,
    UserSettings,
    DailyEntry,
    UserTask,
    UserAchievement,
)
from app.services.stats_service import StatsService

profile_bp = Blueprint("profile", __name__)


def _get_user(user_id: int) -> User:
    return db.session.execute(
        sa.select(User).where(User.id == user_id)
    ).scalar_one()


def _get_or_create_settings(user_id: int) -> UserSettings:
    s = db.session.execute(
        sa.select(UserSettings).where(UserSettings.user_id == user_id)
    ).scalar_one_or_none()
    if s is None:
        s = UserSettings(user_id=user_id)
        db.session.add(s)
        db.session.commit()
    return s


# =========================================================================
# /profile/  — главная
# =========================================================================

@profile_bp.get("/")
@jwt_required()
def index():
    user_id = int(get_jwt_identity())
    user = _get_user(user_id)
    stats = StatsService.get_dashboard_stats(user_id)
    return render_template("profile/index.html", user=user, stats=stats)


# =========================================================================
# /profile/settings
# =========================================================================

@profile_bp.route("/settings", methods=["GET", "POST"])
@jwt_required()
def settings():
    user_id = int(get_jwt_identity())
    settings = _get_or_create_settings(user_id)

    if request.method == "POST":
        # checkboxes отсутствуют в form-data, если выключены
        settings.dark_mode = request.form.get("dark_mode") in ("on", "true", "1", "yes")
        settings.notifications_enabled = request.form.get("notifications_enabled") in (
            "on", "true", "1", "yes",
        )

        from app import SUPPORTED_LOCALES
        lang = (request.form.get("language") or "").strip()
        if lang in SUPPORTED_LOCALES:
            settings.language = lang

        reminder = (request.form.get("daily_reminder_time") or "").strip()
        if reminder == "":
            settings.daily_reminder_time = None
        else:
            # допустимый формат HH:MM (5 символов)
            if (
                len(reminder) == 5
                and reminder[2] == ":"
                and reminder[:2].isdigit()
                and reminder[3:].isdigit()
                and 0 <= int(reminder[:2]) <= 23
                and 0 <= int(reminder[3:]) <= 59
            ):
                settings.daily_reminder_time = reminder
            else:
                flash(_("Invalid reminder time format (HH:MM required)"), "error")
                db.session.rollback()
                return render_template(
                    "profile/settings.html", settings=settings
                ), 400

        db.session.commit()
        flash(_("Settings saved"), "success")
        from app import DEFAULT_LOCALE, LANG_COOKIE, SUPPORTED_LOCALES
        target = settings.language if settings.language in SUPPORTED_LOCALES else DEFAULT_LOCALE
        resp = make_response(redirect(url_for("profile.settings")))
        max_age = 60 * 60 * 24 * 365
        resp.set_cookie(LANG_COOKIE, target, max_age=max_age, samesite="Lax")
        resp.set_cookie("locale", target, max_age=max_age, samesite="Lax")
        return resp

    return render_template("profile/settings.html", settings=settings)


# =========================================================================
# /profile/change-password
# =========================================================================

@profile_bp.route("/change-password", methods=["GET", "POST"])
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())
    user = _get_user(user_id)

    if request.method == "POST":
        current = request.form.get("current_password", "")
        new = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []
        if not user.check_password(current):
            errors.append(_("Current password is incorrect"))
        if len(new) < 8:
            errors.append(_("New password must be at least 8 characters"))
        if new != confirm:
            errors.append(_("New password and confirmation do not match"))
        if new and current and new == current:
            errors.append(_("New password must differ from current"))

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("profile/change_password.html"), 400

        user.set_password(new)
        db.session.commit()
        flash(_("Password changed successfully"), "success")
        return redirect(url_for("profile.index"))

    return render_template("profile/change_password.html")


# =========================================================================
# /profile/export
# =========================================================================

def _gather_export_payload(user_id: int) -> dict:
    user = _get_user(user_id)
    settings = _get_or_create_settings(user_id)

    entries = db.session.execute(
        sa.select(DailyEntry)
        .where(DailyEntry.user_id == user_id)
        .order_by(DailyEntry.date.asc())
    ).scalars().all()

    user_tasks = db.session.execute(
        sa.select(UserTask)
        .where(UserTask.user_id == user_id)
        .order_by(UserTask.assigned_at.asc())
    ).scalars().all()

    achievements = db.session.execute(
        sa.select(UserAchievement).where(UserAchievement.user_id == user_id)
    ).scalars().all()

    stats = StatsService.get_dashboard_stats(user_id)

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "xp": user.xp,
            "level": user.level,
            "streak": user.streak,
            "longest_streak": user.longest_streak,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "settings": {
            "dark_mode": settings.dark_mode,
            "notifications_enabled": settings.notifications_enabled,
            "language": settings.language,
            "daily_reminder_time": settings.daily_reminder_time,
        },
        "stats": stats,
        "entries": [
            {
                "id": e.id,
                "date": e.date.isoformat(),
                "anxiety_level": e.anxiety_level,
                "emotions": e.emotions,
                "text": e.text,
                "ai_analysis": e.ai_analysis,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ],
        "tasks": [
            {
                "task_id": ut.task_id,
                "title": ut.task.title if ut.task else None,
                "difficulty": ut.task.difficulty if ut.task else None,
                "completed": ut.completed,
                "feedback": ut.feedback,
                "assigned_at": ut.assigned_at.isoformat() if ut.assigned_at else None,
                "completed_at": ut.completed_at.isoformat() if ut.completed_at else None,
            }
            for ut in user_tasks
        ],
        "achievements": [
            {
                "name": ua.achievement.name if ua.achievement else None,
                "icon": ua.achievement.icon if ua.achievement else None,
                "earned_at": ua.earned_at.isoformat() if ua.earned_at else None,
            }
            for ua in achievements
        ],
    }


@profile_bp.post("/export")
@jwt_required()
def export_data():
    user_id = int(get_jwt_identity())
    fmt = (request.form.get("format") or "json").lower()
    payload = _gather_export_payload(user_id)

    if fmt == "json":
        body = json.dumps(payload, ensure_ascii=False, indent=2)
        resp = make_response(body)
        resp.headers["Content-Type"] = "application/json; charset=utf-8"
        resp.headers["Content-Disposition"] = (
            'attachment; filename="socialhealth-export.json"'
        )
        return resp

    if fmt == "pdf":
        # HTML-страница, оптимизированная для печати — пользователь делает Ctrl+P → PDF
        html = render_template("profile/export.html", data=payload)
        resp = make_response(html)
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        return resp

    flash(_("Unknown export format"), "error")
    return redirect(url_for("profile.index"))


# =========================================================================
# /profile/delete-account
# =========================================================================

@profile_bp.route("/delete-account", methods=["GET", "POST"])
@jwt_required()
def delete_account():
    user_id = int(get_jwt_identity())
    user = _get_user(user_id)

    if request.method == "POST":
        confirmation = (request.form.get("confirmation") or "").strip()
        password = request.form.get("password") or ""

        if confirmation != "УДАЛИТЬ":
            flash(_("Enter the word 'УДАЛИТЬ' in uppercase to confirm"), "error")
            return render_template("profile/delete_account.html"), 400

        if not user.check_password(password):
            flash(_("Wrong password"), "error")
            return render_template("profile/delete_account.html"), 400

        # cascade=all, delete-orphan на User уже удалит entries/user_tasks/achievements/settings
        db.session.delete(user)
        db.session.commit()

        resp = make_response(redirect(url_for("auth.login")))
        unset_jwt_cookies(resp)
        flash(_("Account deleted"), "success")
        return resp

    return render_template("profile/delete_account.html")
