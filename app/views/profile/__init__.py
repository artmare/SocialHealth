from flask import Blueprint

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/")
def index():
    return "Profile — coming soon"
