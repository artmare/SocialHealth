from flask import Blueprint

progress_bp = Blueprint("progress", __name__)

@progress_bp.route("/")
def index():
    return "Progress — coming soon"
