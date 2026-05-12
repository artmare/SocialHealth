from flask import Blueprint, redirect, url_for

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    """Главная страница - редирект на дашборд"""
    return redirect(url_for("dashboard.index"))