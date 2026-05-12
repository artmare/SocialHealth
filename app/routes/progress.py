from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.stats_service import StatsService

progress_bp = Blueprint("progress", __name__)


@progress_bp.get("/")
@jwt_required()
def index():
    user_id = int(get_jwt_identity())

    stats = StatsService.get_dashboard_stats(user_id)
    comparison = StatsService.get_anxiety_comparison(user_id)
    top_tasks = StatsService.get_top_completed_tasks(user_id, limit=5)
    achievements = StatsService.get_achievements_overview(user_id)

    return render_template(
        "progress/index.html",
        stats=stats,
        comparison=comparison,
        top_tasks=top_tasks,
        achievements=achievements,
    )
