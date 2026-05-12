from flask import Flask, redirect, url_for
from flask_jwt_extended import verify_jwt_in_request


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
    from app.views.sos import sos_bp
    from app.views.profile import profile_bp
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

    @app.get("/")
    def root():
        try:
            verify_jwt_in_request(optional=False)
            return redirect(url_for("dashboard.index"))
        except Exception:
            return redirect(url_for("auth.login"))

    with app.app_context():
        from app import models

    return app
