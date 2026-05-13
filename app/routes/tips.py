from flask import Blueprint, abort, render_template, request

from app.data.tips_data import (
    CATEGORIES,
    DIFFICULTY_LABELS,
    TIPS,
    get_tip,
    get_tips_by_category,
)

tips_bp = Blueprint("tips", __name__)


@tips_bp.get("/")
def index():
    category = request.args.get("category", "all")
    if category not in (set(CATEGORIES.keys()) | {"all"}):
        category = "all"

    tips = get_tips_by_category(category)
    return render_template(
        "tips/index.html",
        tips=tips,
        all_tips=TIPS,
        categories=CATEGORIES,
        difficulty_labels=DIFFICULTY_LABELS,
        active_category=category,
    )


@tips_bp.get("/<identifier>")
def detail(identifier):
    tip = get_tip(identifier)
    if tip is None:
        abort(404)
    return render_template(
        "tips/detail.html",
        tip=tip,
        categories=CATEGORIES,
        difficulty_labels=DIFFICULTY_LABELS,
    )
