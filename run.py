import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

config_name = (
    os.environ.get("FLASK_CONFIG")
    or os.environ.get("FLASK_ENV")
    or "development"
)
app = create_app(config_name)

if __name__ == "__main__":
    app.run()
