from flask import Blueprint

tips_bp = Blueprint("tips", __name__)

@tips_bp.route("/")
def index():
    return "Tips — coming soon"
