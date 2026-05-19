from flask import Flask, g, jsonify, redirect, request, url_for as _flask_url_for
import flask
import sqlalchemy as sa



from config import config_map
from app.extensions import db, jwt, migrate, limiter, csrf, babel


SUPPORTED_LOCALES = ("en", "ru", "uk")
DEFAULT_LOCALE = "en"


def _select_locale():
    """Какой язык активен для текущего запроса."""
    # Сначала смотрим environ — middleware всегда выставляет 'socialhealth.locale'
    # ДО любых before_request hooks.
    try:
        env_loc = request.environ.get("socialhealth.locale")
        if env_loc in SUPPORTED_LOCALES:
            return env_loc
    except Exception:
        pass
    # Резервно — из g (если кто-то выставил позже)
    forced = getattr(g, "locale", None)
    if forced in SUPPORTED_LOCALES:
        return forced
    # Из cookie
    c = request.cookies.get("locale") if request else None
    if c in SUPPORTED_LOCALES:
        return c
    # Authenticated → UserSettings.language
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        verify_jwt_in_request(optional=True)
        ident = get_jwt_identity()
        if ident:
            from app.models import UserSettings
            import sqlalchemy as sa
            s = db.session.execute(
                sa.select(UserSettings).where(UserSettings.user_id == int(ident))
            ).scalar_one_or_none()
            if s and s.language in SUPPORTED_LOCALES:
                return s.language
    except Exception:
        pass
    # Accept-Language
    if request:
        best = request.accept_languages.best_match(list(SUPPORTED_LOCALES))
        if best:
            return best
    return DEFAULT_LOCALE


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map["development"]))

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    csrf.init_app(app)
    babel.init_app(app, locale_selector=_select_locale)

    # ------------------------------------------------------------
    # URL-префикс /ru/ или /uk/ (без префикса = EN дефолт).
    # На before_request снимаем префикс и помечаем locale в g.
    # url_for оборачиваем, чтобы он автоматически добавлял /<locale>
    # для не-EN локали.
    # ------------------------------------------------------------
    # WSGI-middleware: срезает /ru или /en префикс ДО URL-routing.
    _orig_wsgi = app.wsgi_app
    def _locale_prefix_middleware(environ, start_response):
        path = environ.get("PATH_INFO", "")
        detected = DEFAULT_LOCALE
        for code in SUPPORTED_LOCALES:
            if path == f"/{code}" or path.startswith(f"/{code}/"):
                detected = code
                rest = path[len(f"/{code}"):] or "/"
                environ["PATH_INFO"] = rest
                break
        environ["socialhealth.locale"] = detected
        return _orig_wsgi(environ, start_response)
    app.wsgi_app = _locale_prefix_middleware

    @app.before_request
    def _copy_locale_from_environ():
        g.locale = request.environ.get("socialhealth.locale", DEFAULT_LOCALE)
        # Сбрасываем babel-кэш, чтобы Flask-Babel переспросил locale_selector
        # на текущем запросе (важно когда test_client использует один процесс).
        if hasattr(g, "_flask_babel"):
            try:
                del g._flask_babel.babel_locale
            except AttributeError:
                pass
            try:
                del g._flask_babel.babel_translations
            except AttributeError:
                pass

    @app.before_request
    def _clear_stale_jwt_user():
        """Handle cookies that point to a user missing from an ephemeral DB."""
        try:
            from flask_jwt_extended import get_jwt_identity, unset_jwt_cookies, verify_jwt_in_request
            verify_jwt_in_request(optional=True)
            ident = get_jwt_identity()
            if not ident:
                return None

            from app.models import User
            exists = db.session.scalar(
                sa.select(sa.func.count(User.id)).where(User.id == int(ident))
            )
            if exists:
                return None
        except Exception:
            return None

        if request.path.startswith("/api/"):
            return jsonify(error="unauthorized", reason="user no longer exists"), 401

        resp = redirect(_flask_url_for("auth.login"))
        unset_jwt_cookies(resp)
        resp.delete_cookie("locale")
        return resp

    # Безопасный url_for с автодобавлением /<locale> для не-EN.
    _orig_url_for = flask.url_for

    def _url_for_with_locale(endpoint, **values):
        # Кто-то явно указал _lang → используем его (для переключателя языка)
        lang = values.pop("_lang", None) or getattr(g, "locale", DEFAULT_LOCALE)
        if lang not in SUPPORTED_LOCALES:
            lang = DEFAULT_LOCALE
        url = _orig_url_for(endpoint, **values)
        # static-файлы и абсолютные внешние ссылки без изменений
        if endpoint == "static" or url.startswith(("http://", "https://", "tel:", "mailto:")):
            return url
        if lang == DEFAULT_LOCALE:
            return url
        # url начинается с / (относительный)
        if url.startswith("/"):
            return f"/{lang}{url}"
        return url

    # Подменяем url_for и в Flask, и в Jinja-окружении
    flask.url_for = _url_for_with_locale
    app.jinja_env.globals["url_for"] = _url_for_with_locale

    @app.context_processor
    def _inject_locale():
        return {
            "current_locale": getattr(g, "locale", DEFAULT_LOCALE),
            "supported_locales": list(SUPPORTED_LOCALES),
        }

    @app.template_global("switch_locale_url")
    def _switch_locale_url(target_lang):
        """URL текущей страницы в другой локали."""
        # request.full_path уже без префикса (срезали в before_request),
        # поэтому собираем заново
        path = request.environ.get("PATH_INFO", "/")
        qs = request.query_string.decode("utf-8", errors="replace")
        prefix = "" if target_lang == DEFAULT_LOCALE else f"/{target_lang}"
        return prefix + path + (("?" + qs) if qs else "")

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.diary import diary_bp
    from app.routes.tasks import tasks_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.progress import progress_bp
    from app.routes.sos import sos_bp
    from app.routes.profile import profile_bp
    from app.routes.tips import tips_bp
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
        # /api/* → всегда 401 JSON.
        if request.path.startswith("/api/"):
            return jsonify(error="unauthorized", reason=str(reason)), 401
        # AJAX (X-Requested-With: XMLHttpRequest или fetch с Accept: application/json) → 401 JSON.
        is_xhr = (
            request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or "application/json" in (request.accept_mimetypes.best or "")
            and "text/html" not in (request.accept_mimetypes.best or "")
        )
        if is_xhr:
            return jsonify(error="unauthorized", reason=str(reason)), 401
        # /auth/refresh — отдельный API-эндпоинт, отдаём JSON (его дёргает только JS).
        if request.path.endswith("/auth/refresh") or request.path.endswith("/auth/logout"):
            return jsonify(error="unauthorized", reason=str(reason)), 401
        # Браузерная навигация (GET / POST / PUT / DELETE с Accept: text/html) → редирект.
        return redirect(_flask_url_for("auth.login"))

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

    from app.database import prepare_database
    prepare_database(app)

    return app
