from flask import Blueprint

sos_bp = Blueprint("sos", __name__)

@sos_bp.route("/")
def index():
    return "SOS — coming soon"
