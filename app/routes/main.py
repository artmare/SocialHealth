from flask import Blueprint, redirect, url_for
from flask_jwt_extended import verify_jwt_in_request

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    """Главная: для залогиненных → /dashboard/, для гостей → /auth/login."""
    try:
        verify_jwt_in_request(optional=False)
        return redirect(url_for("dashboard.index"))
    except Exception:
        return redirect(url_for("auth.login"))
