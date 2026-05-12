from flask import Flask, jsonify, redirect, request, url_for



from config import config_map
from app.extensions import db, jwt, migrate, limiter, csrf


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map["development"]))

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    csrf.init_app(app)

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.diary import diary_bp
    from app.routes.tasks import tasks_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.progress import progress_bp
    from app.routes.sos import sos_bp
    from app.routes.profile import profile_bp
    from app.views.tips import tips_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(diary_bp, url_prefix="/diary")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(progress_bp, url_prefix="/progress")
    app.register_blueprint(sos_bp, url_prefix="/sos")
    app.register_blueprint(profile_bp, url_prefix="/profile")
    app.register_blueprint(tips_bp, url_prefix="/tips")
    app.register_blueprint(api_bp, url_prefix="/api")

    def _auth_failure(reason):
        # HTML-навигация (GET с Accept: text/html и не /api/) → редирект на логин;
        # всё остальное (API, AJAX, POST/PUT/DELETE, /auth/refresh и т.п.) → 401 JSON.
        wants_html = (
            request.method == "GET"
            and not request.path.startswith("/api/")
            and "text/html" in (request.accept_mimetypes.best or "")
        )
        if not wants_html:
            return jsonify(error="unauthorized", reason=str(reason)), 401
        return redirect(url_for("auth.login"))

    @jwt.unauthorized_loader
    def _on_missing(reason):
        return _auth_failure(reason)

    @jwt.invalid_token_loader
    def _on_invalid(reason):
        return _auth_failure(reason)

    @jwt.expired_token_loader
    def _on_expired(_jwt_header, _jwt_data):
        return _auth_failure("token expired")









    with app.app_context():
        from app import models

    return app
