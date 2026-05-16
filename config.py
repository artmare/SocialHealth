import os
import tempfile
from pathlib import Path


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _vercel_sqlite_fallback() -> str:
    db_path = Path(tempfile.gettempdir()) / "socialhealth.db"
    return f"sqlite:///{db_path.as_posix()}"


class BaseConfig:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY", "dev-secret-key-change-before-production"
    )
    JWT_SECRET_KEY = os.environ.get(
        "JWT_SECRET_KEY", "dev-jwt-secret-change-before-production"
    )
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    JWT_REFRESH_TOKEN_EXPIRES = 2592000
    JWT_TOKEN_LOCATION = ["cookies", "headers"]
    JWT_ACCESS_COOKIE_NAME = "access_token_cookie"
    JWT_REFRESH_COOKIE_NAME = "refresh_token_cookie"
    JWT_COOKIE_SECURE = _env_bool("SECURE_COOKIES")
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_CSRF_PROTECT = False
    SESSION_COOKIE_SECURE = _env_bool("SECURE_COOKIES")
    SESSION_COOKIE_SAMESITE = "Lax"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    RATELIMIT_STORAGE_URI = "memory://"

    BABEL_DEFAULT_LOCALE = "en"
    BABEL_DEFAULT_TIMEZONE = "UTC"
    BABEL_TRANSLATION_DIRECTORIES = "translations"
    SUPPORTED_LOCALES = ["en", "ru", "uk"]

    XP_LEVELS = [0, 100, 250, 500, 900, 1400, 2000, 2800, 3800, 5000]
    LEVEL_TITLES_BY_LOCALE = {
        "en": [
            "Novice", "Seeker", "Observer", "Brave Soul", "Overcomer",
            "Warrior", "Master", "Hero", "Legend", "Anxiety Lord",
        ],
        "ru": [
            "Новичок", "Искатель", "Наблюдатель", "Смельчак", "Преодолевший",
            "Воин", "Мастер", "Герой", "Легенда", "Властелин тревоги",
        ],
        "uk": [
            "Новачок", "Шукач", "Спостерігач", "Сміливець", "Той, хто долає",
            "Воїн", "Майстер", "Герой", "Легенда", "Володар тривоги",
        ],
    }
    # Backward-compat: дефолт — EN
    LEVEL_TITLES = LEVEL_TITLES_BY_LOCALE["en"]

    @classmethod
    def get_level_from_xp(cls, xp: int) -> int:
        level = 0
        for threshold in cls.XP_LEVELS:
            if xp >= threshold:
                level += 1
            else:
                break
        return level


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///socialhealth.db"
    )
    RATELIMIT_STORAGE_URI = "memory://"


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or (_vercel_sqlite_fallback() if os.environ.get("VERCEL") else None)
        or "postgresql://user:password@localhost:5432/socialhealth"
    )
    JWT_COOKIE_SECURE = _env_bool("SECURE_COOKIES", default=True)
    SESSION_COOKIE_SECURE = _env_bool("SECURE_COOKIES", default=True)
    RATELIMIT_STORAGE_URI = os.environ.get(
        "RATELIMIT_STORAGE_URI", "memory://"
    )


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
