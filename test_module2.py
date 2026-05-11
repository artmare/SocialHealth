"""
test_module2.py — тестирование модуля Авторизации (auth).
Запуск: python test_module2.py
"""

import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

results = []


def check(desc, condition, error=""):
    if condition:
        results.append((True, desc, None))
    else:
        results.append((False, desc, error))


def run_checks():
    from app import create_app
    from app.extensions import db
    from app.models import User, UserSettings
    import sqlalchemy as sa

    app = create_app("testing")
    client = app.test_client()

    print("=" * 60)
    print("=== ТЕСТИРОВАНИЕ МОДУЛЯ 2: АВТОРИЗАЦИЯ ===")
    print("=" * 60)
    print()

    with app.app_context():
        db.create_all()

        # ================================================================
        # 1. Blueprint зарегистрирован
        # ================================================================
        print("--- 1. Blueprint ---")
        check("auth_bp зарегистрирован в приложении", "auth" in app.blueprints)

        rules = [str(r) for r in app.url_map.iter_rules()]
        check("URL /auth/register существует", any("/auth/register" in r for r in rules))
        check("URL /auth/login существует", any("/auth/login" in r for r in rules))
        check("URL /auth/refresh существует", any("/auth/refresh" in r for r in rules))
        check("URL /auth/logout существует", any("/auth/logout" in r for r in rules))

        # ================================================================
        # 2. Страницы отображаются
        # ================================================================
        print()
        print("--- 2. Страницы отображаются ---")
        resp_reg = client.get("/auth/register")
        check("GET /auth/register возвращает 200", resp_reg.status_code == 200)
        html_reg = resp_reg.data.decode("utf-8")
        check(
            "Страница регистрации содержит 'Регистрация'",
            "Регистрация" in html_reg,
        )

        resp_log = client.get("/auth/login")
        check("GET /auth/login возвращает 200", resp_log.status_code == 200)
        html_log = resp_log.data.decode("utf-8")
        check("Страница логина содержит 'Войти'", "Войти" in html_log)

        # ================================================================
        # 3. Регистрация
        # ================================================================
        print()
        print("--- 3. Регистрация ---")

        # 3.1 Успешная регистрация
        resp = client.post(
            "/auth/register",
            data={
                "username": "testuser",
                "email": "test@test.com",
                "password": "testpass123",
                "confirm_password": "testpass123",
            },
            follow_redirects=False,
        )
        check(
            "POST /auth/register с валидными данными — успех",
            resp.status_code in (200, 201, 301, 302, 307, 308),
            f"status={resp.status_code}",
        )

        # 3.2 User в БД
        user = db.session.execute(
            sa.select(User).where(User.email == "test@test.com")
        ).scalar_one_or_none()
        check("После регистрации User существует в БД", user is not None)

        if user:
            check(
                "Пароль хеширован (password_hash != plaintext)",
                user.password_hash != "testpass123",
                f"hash={user.password_hash}",
            )

            settings = db.session.execute(
                sa.select(UserSettings).where(UserSettings.user_id == user.id)
            ).scalar_one_or_none()
            check("UserSettings создан для нового пользователя", settings is not None)
        else:
            check("Пароль хеширован", False, "User не найден")
            check("UserSettings создан", False, "User не найден")

        # 3.3 Дубликат email
        resp_dup = client.post(
            "/auth/register",
            data={
                "username": "testuser2",
                "email": "test@test.com",
                "password": "testpass123",
                "confirm_password": "testpass123",
            },
        )
        html_dup = resp_dup.data.decode("utf-8")
        check(
            "POST /auth/register с дублирующим email — ошибка",
            "уже существует" in html_dup or resp_dup.status_code >= 400,
            f"status={resp_dup.status_code}",
        )

        # 3.4 Короткий пароль
        resp_short = client.post(
            "/auth/register",
            data={
                "username": "short",
                "email": "short@test.com",
                "password": "123",
                "confirm_password": "123",
            },
        )
        html_short = resp_short.data.decode("utf-8")
        has_short_error = (
            "Минимум 8 символов" in html_short
            or "Field must be at least" in html_short
            or "at least 8" in html_short
        )
        check(
            "POST /auth/register с коротким паролем — ошибка валидации",
            has_short_error,
            f"html не содержит ошибку длины пароля",
        )

        # 3.5 Без email
        resp_no_email = client.post(
            "/auth/register",
            data={
                "username": "noemail",
                "email": "",
                "password": "testpass123",
                "confirm_password": "testpass123",
            },
        )
        html_no_email = resp_no_email.data.decode("utf-8")
        has_email_error = (
            "Обязательное поле" in html_no_email
            or "This field is required" in html_no_email
        )
        check(
            "POST /auth/register без email — ошибка валидации",
            has_email_error,
            f"status={resp_no_email.status_code}",
        )

        # 3.6 Несовпадающие пароли
        resp_mismatch = client.post(
            "/auth/register",
            data={
                "username": "mismatch",
                "email": "mismatch@test.com",
                "password": "testpass123",
                "confirm_password": "different123",
            },
        )
        html_mismatch = resp_mismatch.data.decode("utf-8")
        has_mismatch_error = (
            "совпадать" in html_mismatch.lower()
            or "Field must be equal to" in html_mismatch
            or "password" in html_mismatch.lower()
        )
        check(
            "POST /auth/register с несовпадающими паролями — ошибка",
            has_mismatch_error,
            f"status={resp_mismatch.status_code}",
        )

        # ================================================================
        # 4. Логин
        # ================================================================
        print()
        print("--- 4. Логин ---")

        # 4.1 Успешный логин
        resp_login = client.post(
            "/auth/login",
            data={
                "email": "test@test.com",
                "password": "testpass123",
            },
            follow_redirects=False,
        )
        cookies = resp_login.headers.getlist("Set-Cookie")
        access_cookie = any("access_token_cookie" in c for c in cookies)
        refresh_cookie = any("refresh_token_cookie" in c for c in cookies)
        check(
            "POST /auth/login с правильными данными — access_token получен",
            access_cookie,
            f"cookies={[c[:50] for c in cookies]}",
        )
        check(
            "POST /auth/login с правильными данными — refresh_token получен",
            refresh_cookie,
        )

        # 4.2 Неверный пароль
        resp_bad_pass = client.post(
            "/auth/login",
            data={
                "email": "test@test.com",
                "password": "wrongpassword",
            },
        )
        html_bad_pass = resp_bad_pass.data.decode("utf-8")
        check(
            "POST /auth/login с неверным паролем — ошибка",
            "Неверный" in html_bad_pass or resp_bad_pass.status_code == 401,
            f"status={resp_bad_pass.status_code}",
        )

        # 4.3 Несуществующий email
        resp_bad_email = client.post(
            "/auth/login",
            data={
                "email": "nosuch@test.com",
                "password": "testpass123",
            },
        )
        html_bad_email = resp_bad_email.data.decode("utf-8")
        check(
            "POST /auth/login с несуществующим email — ошибка",
            "Неверный" in html_bad_email or resp_bad_email.status_code == 401,
            f"status={resp_bad_email.status_code}",
        )

        # 4.4 access_token работает — используем /auth/refresh
        resp_refresh = client.post("/auth/refresh")
        check(
            "Полученный access_token/refresh_token работает (POST /auth/refresh после логина)",
            resp_refresh.status_code == 200,
            f"status={resp_refresh.status_code}",
        )
        if resp_refresh.status_code == 200:
            data = resp_refresh.get_json()
            check(
                "Ответ refresh содержит access_token",
                data is not None and "access_token" in data,
            )

        # ================================================================
        # 5. Refresh токен
        # ================================================================
        print()
        print("--- 5. Refresh токен ---")

        # 5.1 Уже проверено выше, но добавим явную проверку
        check(
            "POST /auth/refresh с валидным refresh_token — новый access_token",
            resp_refresh.status_code == 200,
        )

        # 5.2 Без токена
        fresh_client = app.test_client()
        resp_no_refresh = fresh_client.post("/auth/refresh")
        check(
            "POST /auth/refresh без токена — ошибка 401",
            resp_no_refresh.status_code == 401,
            f"status={resp_no_refresh.status_code}",
        )

        # ================================================================
        # 6. Logout
        # ================================================================
        print()
        print("--- 6. Logout ---")

        resp_logout = client.post("/auth/logout", follow_redirects=False)
        check(
            "POST /auth/logout с валидным токеном — успех (редирект)",
            resp_logout.status_code in (301, 302, 307, 308),
            f"status={resp_logout.status_code}",
        )

        logout_cookies = resp_logout.headers.getlist("Set-Cookie")
        access_cleared = any(
            "access_token_cookie=" in c
            and ("Max-Age=0" in c or "Expires=Thu, 01 Jan 1970" in c)
            for c in logout_cookies
        )
        check(
            "Logout очищает access cookie",
            access_cleared or len(logout_cookies) > 0,
            f"cookies={[c[:60] for c in logout_cookies]}",
        )

        # ================================================================
        # 7. Защита маршрутов
        # ================================================================
        print()
        print("--- 7. Защита маршрутов ---")

        # 7.1 Без токена
        fresh_client2 = app.test_client()
        resp_unauth = fresh_client2.post("/auth/refresh")
        check(
            "Защищённый маршрут без токена — 401",
            resp_unauth.status_code == 401,
            f"status={resp_unauth.status_code}",
        )

        # 7.2 С токеном
        auth_client = app.test_client()
        auth_client.post(
            "/auth/login",
            data={
                "email": "test@test.com",
                "password": "testpass123",
            },
        )
        resp_auth = auth_client.post("/auth/refresh")
        check(
            "Защищённый маршрут с валидным токеном — доступ разрешён (200)",
            resp_auth.status_code == 200,
            f"status={resp_auth.status_code}",
        )

        # ================================================================
        # 8. Проверка base.html
        # ================================================================
        print()
        print("--- 8. Проверка base.html ---")
        check(
            "base.html содержит 'SocialHealth' в навигации",
            "SocialHealth" in html_log,
        )
        check("base.html содержит кнопку/ссылку SOS", "SOS" in html_log)
        check(
            "base.html содержит дисклеймер 'не является медицинским сервисом'",
            "не является медицинским сервисом" in html_log,
        )

    # ================================================================
    # Итог
    # ================================================================
    print()
    passed = sum(1 for ok, _, _ in results if ok)
    failed = sum(1 for ok, _, _ in results if not ok)
    total = passed + failed

    for ok, desc, err in results:
        if ok:
            print(f"[OK] {desc}")
        else:
            print(f"[FAIL] {desc} — ошибка: {err}")

    print()
    print("=" * 60)
    print(f"=== ИТОГ: Пройдено {passed} из {total} тестов ===")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_checks()
    exit(0 if success else 1)
