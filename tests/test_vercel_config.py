import importlib

import pytest


def _reload_config(monkeypatch, **env):
    for key in (
        "VERCEL",
        "RAILWAY_ENVIRONMENT",
        "DATABASE_URL",
        "POSTGRES_URL",
        "POSTGRES_PRISMA_URL",
        "ALLOW_TMP_SQLITE",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    import config

    return importlib.reload(config)


def test_vercel_requires_persistent_database(monkeypatch):
    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        _reload_config(monkeypatch, VERCEL="1")


def test_railway_requires_persistent_database(monkeypatch):
    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        _reload_config(monkeypatch, RAILWAY_ENVIRONMENT="production")


def test_vercel_uses_database_url_when_set(monkeypatch):
    config = _reload_config(
        monkeypatch,
        VERCEL="1",
        DATABASE_URL="postgresql://user:pass@example.com:5432/socialhealth",
    )

    assert (
        config.ProductionConfig.SQLALCHEMY_DATABASE_URI
        == "postgresql://user:pass@example.com:5432/socialhealth"
    )


def test_vercel_uses_postgres_url_when_database_url_is_missing(monkeypatch):
    config = _reload_config(
        monkeypatch,
        VERCEL="1",
        POSTGRES_URL="postgres://user:pass@example.com:5432/socialhealth",
    )

    assert (
        config.ProductionConfig.SQLALCHEMY_DATABASE_URI
        == "postgresql://user:pass@example.com:5432/socialhealth"
    )


def test_tmp_sqlite_requires_explicit_opt_in(monkeypatch):
    config = _reload_config(
        monkeypatch,
        VERCEL="1",
        ALLOW_TMP_SQLITE="true",
    )

    assert config.ProductionConfig.SQLALCHEMY_DATABASE_URI.startswith("sqlite:///")
