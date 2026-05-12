from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import csrf
from app.services.stats_service import StatsService

api_bp = Blueprint("api", __name__)
csrf.exempt(api_bp)


@api_bp.get("/stats/summary")
@jwt_required()
def summary():
    user_id = int(get_jwt_identity())
    return jsonify(StatsService.get_dashboard_stats(user_id))


@api_bp.get("/stats/anxiety")
@jwt_required()
def anxiety():
    user_id = int(get_jwt_identity())
    days = request.args.get("days", 30, type=int)
    if days < 1:
        days = 1
    if days > 365:
        days = 365
    return jsonify(StatsService.get_anxiety_history(user_id, days=days))


@api_bp.get("/stats/tasks")
@jwt_required()
def tasks():
    user_id = int(get_jwt_identity())
    weeks = request.args.get("weeks", 8, type=int)
    if weeks < 1:
        weeks = 1
    if weeks > 52:
        weeks = 52
    return jsonify(StatsService.get_tasks_by_week(user_id, weeks=weeks))


@api_bp.get("/stats/comparison")
@jwt_required()
def comparison():
    user_id = int(get_jwt_identity())
    return jsonify(StatsService.get_anxiety_comparison(user_id))
