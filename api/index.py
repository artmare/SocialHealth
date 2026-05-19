import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("FLASK_CONFIG", "production")
os.environ.setdefault("SECURE_COOKIES", "true")

from app import create_app
from app.extensions import db
from app.models import Task


app = create_app(os.environ.get("FLASK_CONFIG", "production"))


def _prepare_tmp_sqlite() -> None:
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not (
        os.environ.get("VERCEL")
        and os.environ.get("ALLOW_TMP_SQLITE")
        and db_uri.startswith("sqlite:///")
    ):
        return

    with app.app_context():
        db.create_all()
        if Task.query.count() == 0:
            from seed_tasks import seed

            seed(app)


_prepare_tmp_sqlite()
