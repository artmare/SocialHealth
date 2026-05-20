import os

from sqlalchemy import text

from app.extensions import db


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def should_prepare_database() -> bool:
    return env_bool("AUTO_INIT_DB", default=False)


def prepare_database(app) -> None:
    if not should_prepare_database():
        return

    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite:///") and not env_bool("ALLOW_TMP_SQLITE"):
        return

    with app.app_context():
        from app.models import Task
        import seed_tasks

        allow_schema_create = env_bool("ALLOW_SCHEMA_CREATE") or (
            db_uri.startswith("sqlite:///") and env_bool("ALLOW_TMP_SQLITE")
        )
        if allow_schema_create:
            db.create_all()
        is_postgres = db.engine.url.get_backend_name().startswith("postgres")
        if is_postgres:
            db.session.execute(text("SELECT pg_advisory_lock(73310420)"))
        try:
            if Task.query.count() < len(seed_tasks.TASKS):
                seed_tasks.seed(app)
        finally:
            if is_postgres:
                db.session.execute(text("SELECT pg_advisory_unlock(73310420)"))
                db.session.commit()
