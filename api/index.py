import os
import sys
from pathlib import Path

from sqlalchemy import text


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("FLASK_CONFIG", "production")
os.environ.setdefault("SECURE_COOKIES", "true")

from app import create_app
from app.extensions import db
from app.models import Task


app = create_app(os.environ.get("FLASK_CONFIG", "production"))


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _should_prepare_database() -> bool:
    return _env_bool("AUTO_INIT_DB", default=bool(os.environ.get("VERCEL")))


def _prepare_database() -> None:
    if not _should_prepare_database():
        return

    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite:///") and not _env_bool("ALLOW_TMP_SQLITE"):
        return

    with app.app_context():
        db.create_all()
        is_postgres = db.engine.url.get_backend_name().startswith("postgres")
        if is_postgres:
            db.session.execute(text("SELECT pg_advisory_lock(73310420)"))
        try:
            import seed_tasks

            if Task.query.count() < len(seed_tasks.TASKS):
                seed_tasks.seed(app)
        finally:
            if is_postgres:
                db.session.execute(text("SELECT pg_advisory_unlock(73310420)"))
                db.session.commit()


_prepare_database()
