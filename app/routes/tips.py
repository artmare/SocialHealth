from flask import Blueprint, abort, render_template, request

from app.data.tips_data import (
    CATEGORIES,
    DIFFICULTY_LABELS,
    TIPS,
    get_tip,
    get_tips_by_category,
    localized_categories,
    localized_difficulty_labels,
    _apply_locale,
)

tips_bp = Blueprint("tips", __name__)


@tips_bp.get("/")
def index():
    cats = localized_categories()
    category = request.args.get("category", "all")
    if category not in (set(cats.keys()) | {"all"}):
        category = "all"

    tips = get_tips_by_category(category)
    all_tips = [_apply_locale(t) for t in TIPS]
    return render_template(
        "tips/index.html",
        tips=tips,
        all_tips=all_tips,
        categories=cats,
        difficulty_labels=localized_difficulty_labels(),
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
        categories=localized_categories(),
        difficulty_labels=localized_difficulty_labels(),
    )
