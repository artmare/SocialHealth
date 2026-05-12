from flask import Blueprint, render_template

sos_bp = Blueprint("sos", __name__)


@sos_bp.get("/")
def index():
    return render_template("sos/index.html")


@sos_bp.get("/breathing")
def breathing():
    return render_template("sos/breathing.html")


@sos_bp.get("/grounding")
def grounding():
    return render_template("sos/grounding.html")
