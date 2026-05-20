from datetime import date
from typing import Optional

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
)
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_babel import lazy_gettext as _
import sqlalchemy as sa

from app.extensions import db
from app.models import DailyEntry
from app.emotions import EMOTIONS, normalize_emotions
from app.services.achievement_service import AchievementService
from app.services.ai_service import AIService

diary_bp = Blueprint("diary", __name__, template_folder="../templates/diary")


@diary_bp.get("/new")
@jwt_required()
def new():
    return render_template("new.html", emotions=EMOTIONS)


@diary_bp.post("/new")
@jwt_required()
def create():
    user_id = int(get_jwt_identity())

    anxiety_raw = request.form.get("anxiety_level", "").strip()
    try:
        anxiety_level = int(anxiety_raw)
    except ValueError:
        flash(_("Anxiety level must be a number"), "error")
        return render_template("new.html", emotions=EMOTIONS), 400

    if not (1 <= anxiety_level <= 10):
        flash(_("Anxiety level must be between 1 and 10"), "error")
        return render_template("new.html", emotions=EMOTIONS), 400

    emotions = normalize_emotions(request.form.getlist("emotions"))
    text = request.form.get("text", "").strip()

    if not text:
        flash(_("Please describe your experience"), "error")
        return render_template("new.html", emotions=EMOTIONS), 400

    if len(text) > 2000:
        text = text[:2000]

    entry = DailyEntry(
        user_id=user_id,
        date=date.today(),
        anxiety_level=anxiety_level,
        emotions=emotions if emotions else None,
        text=text,
    )
    db.session.add(entry)
    db.session.commit()

    try:
        analysis = AIService.analyze_entry(text, anxiety_level)
        entry.ai_analysis = analysis
        db.session.commit()
    except Exception:
        entry.ai_analysis = {"error": str(_("Analysis is temporarily unavailable"))}
        db.session.commit()

    AchievementService.award_for_user(user_id)
    flash(_("Entry saved"), "success")
    return redirect(url_for("diary.index"))


@diary_bp.get("/")
@jwt_required()
def index():
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1

    per_page = 10

    total = db.session.scalar(
        sa.select(sa.func.count(DailyEntry.id)).where(DailyEntry.user_id == user_id)
    )

    entries = db.session.execute(
        sa.select(DailyEntry)
        .where(DailyEntry.user_id == user_id)
        .order_by(DailyEntry.date.desc(), DailyEntry.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).scalars().all()

    total_pages = (total + per_page - 1) // per_page if total else 1

    return render_template(
        "list.html",
        entries=entries,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@diary_bp.get("/<int:entry_id>")
@jwt_required()
def detail(entry_id: int):
    user_id = int(get_jwt_identity())

    entry = db.session.execute(
        sa.select(DailyEntry).where(
            DailyEntry.id == entry_id,
            DailyEntry.user_id == user_id,
        )
    ).scalar_one_or_none()

    if entry is None:
        abort(404)

    return render_template("detail.html", entry=entry)
