import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("FLASK_CONFIG", "production")
os.environ.setdefault("SECURE_COOKIES", "true")

from app import create_app


app = create_app(os.environ.get("FLASK_CONFIG", "production"))
