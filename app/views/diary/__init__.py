from flask import Blueprint

diary_bp = Blueprint("diary", __name__)

@diary_bp.route("/")
def index():
    return "Diary — coming soon"
