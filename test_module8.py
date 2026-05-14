"""
test_module8.py — тестирование модуля 8 (профиль и настройки).
Запуск: python test_module8.py
"""

import sys
import os
import re
import json

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from datetime import date, datetime, timedelta, timezone

results = []


def check(desc, condition, error=""):
    if condition:
        results.append((True, desc, None))
    else:
        results.append((False, desc, error))


def read_file(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def login_client(app, email, password):
    c = app.test_client()
    c.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
    return c


def make_user(db, User, UserSettings, username, email, password, **kw):
    u = User(username=username, email=email, **kw)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    s = UserSettings(user_id=u.id)
    db.session.add(s)
    db.session.commit()
    return u


def run_checks():
    from app import create_app
    from app.extensions import db
    from app.models import (
        User,
        UserSettings,
        DailyEntry,
        Task,
        UserTask,
        Achievement,
        UserAchievement,
    )
    import sqlalchemy as sa

    app = create_app("testing")

    print("=" * 60)
    print("=== ТЕСТИРОВАНИЕ МОДУЛЯ 8: ПРОФИЛЬ И НАСТРОЙКИ ===")
    print("=" * 60)
    print()

    with app.app_context():
        db.create_all()

        # ============================================================
        # 1. Blueprint и маршруты
        # ============================================================
        print("--- 1. Blueprint и маршруты ---")
        check("Blueprint profile зарегистрирован", "profile" in app.blueprints)
        rules = {str(r.rule) for r in app.url_map.iter_rules()}
        for url in [
            "/profile/",
            "/profile/settings",
            "/profile/change-password",
            "/profile/export",
            "/profile/delete-account",
        ]:
            check(f"URL {url} существует", url in rules,
                  f"profile rules: {sorted(r for r in rules if r.startswith('/profile'))}")

        # ============================================================
        # 2. Защита маршрутов
        # ============================================================
        print()
        print("--- 2. Защита маршрутов без токена ---")
        anon = app.test_client()
        for url in ["/profile/", "/profile/settings"]:
            r = anon.get(url, follow_redirects=False)
            check(
                f"GET {url} без токена → 401 или редирект",
                r.status_code in (401, 301, 302, 307, 308),
                f"status={r.status_code}",
            )
        for url in ["/profile/change-password", "/profile/export"]:
            r = anon.post(url, follow_redirects=False)
            check(
                f"POST {url} без токена → 401 или редирект",
                r.status_code in (401, 301, 302, 307, 308),
                f"status={r.status_code}",
            )

        # ============================================================
        # 3-4. Страница профиля + статистика
        # ============================================================
        print()
        print("--- 3-4. Страница профиля + статистика ---")
        u3 = make_user(
            db, User, UserSettings, "alice8", "alice8@test.com", "pass1234",
            xp=250, level=3, streak=10,
        )
        today = date.today()
        for i, lvl in enumerate([3, 4, 5, 6, 7]):
            db.session.add(DailyEntry(
                user_id=u3.id, date=today - timedelta(days=i),
                anxiety_level=lvl, text=f"e{i}",
            ))
        t_easy = Task(title="T1", description="d", category="breathing",
                      difficulty="easy", xp_reward=10)
        db.session.add(t_easy); db.session.commit()
        for i in range(3):
            db.session.add(UserTask(
                user_id=u3.id, task_id=t_easy.id, completed=True,
                completed_at=datetime.now(timezone.utc) - timedelta(hours=i),
            ))
        db.session.commit()

        c3 = login_client(app, "alice8@test.com", "pass1234")
        r = c3.get("/ru/profile/", headers={"Accept": "text/html"})
        check("/profile/ с токеном → 200", r.status_code == 200, f"status={r.status_code}")
        html = r.data.decode("utf-8")
        check("Профиль содержит email/username",
              "alice8" in html or "alice8@test.com" in html)
        check("Профиль содержит уровень (level)",
              "Уровень" in html or "level" in html.lower())
        check("Профиль содержит XP", "XP" in html or "xp" in html)
        check("Профиль содержит количество заданий",
              "Заданий" in html or "заданий" in html.lower() or "Tasks completed" in html or "tasks completed" in html.lower()
              or "Выполнено" in html)
        check("Профиль содержит количество записей",
              "Записей" in html or "записей" in html.lower() or "Diary entries" in html or "diary entries" in html.lower())
        check("Профиль содержит ссылку на /profile/change-password",
              "/profile/change-password" in html)
        check("Профиль содержит ссылку на /profile/settings",
              "/profile/settings" in html)

        # значения статистики на странице
        check("Профиль показывает XP=250", re.search(r"\b250\b", html) is not None)
        check("Профиль показывает уровень=3",
              re.search(r"Уровень[^<]*<[^>]*>\s*3", html, re.IGNORECASE) is not None
              or "Уровень</div>\n            <div class=\"value\">3" in html
              or re.search(r">\s*3\s*<", html) is not None)
        check("Профиль показывает заданий=3",
              re.search(r">\s*3\s*<", html) is not None)
        check("Профиль показывает записей=5",
              re.search(r">\s*5\s*<", html) is not None)

        # ============================================================
        # 5. Смена пароля
        # ============================================================
        print()
        print("--- 5. Смена пароля ---")
        u5 = make_user(db, User, UserSettings,
                       "pwd5", "pwd5@test.com", "oldpass1")
        c5 = login_client(app, "pwd5@test.com", "oldpass1")

        # 5.1 Успешная смена
        r = c5.post("/ru/profile/change-password", data={
            "current_password": "oldpass1",
            "new_password": "newpass123",
            "confirm_password": "newpass123",
        }, follow_redirects=False)
        check("Смена пароля при корректных данных → редирект (успех)",
              r.status_code in (301, 302, 303, 307, 308),
              f"status={r.status_code}")

        u5_fresh = db.session.execute(
            sa.select(User).where(User.id == u5.id)
        ).scalar_one()
        check("После смены: check_password('newpass123') == True",
              u5_fresh.check_password("newpass123"))
        check("После смены: check_password(старый) == False",
              not u5_fresh.check_password("oldpass1"))

        # 5.2 Перелогинимся новым паролем для следующих тестов
        c5b = login_client(app, "pwd5@test.com", "newpass123")

        # 5.3 Неверный текущий
        r = c5b.post("/ru/profile/change-password", data={
            "current_password": "wrongCurrent",
            "new_password": "anotherpass1",
            "confirm_password": "anotherpass1",
        }, follow_redirects=False)
        check("Неверный текущий пароль → не редирект (ошибка)",
              r.status_code not in (301, 302, 303, 307, 308),
              f"status={r.status_code}")
        u5_check = db.session.execute(
            sa.select(User).where(User.id == u5.id)
        ).scalar_one()
        check("После ошибки пароль НЕ изменился",
              u5_check.check_password("newpass123"))

        # 5.4 Короткий новый
        r = c5b.post("/ru/profile/change-password", data={
            "current_password": "newpass123",
            "new_password": "short",
            "confirm_password": "short",
        }, follow_redirects=False)
        check("Короткий пароль (<8) → ошибка",
              r.status_code not in (301, 302, 303, 307, 308),
              f"status={r.status_code}")

        # 5.5 Несовпадающее подтверждение
        r = c5b.post("/ru/profile/change-password", data={
            "current_password": "newpass123",
            "new_password": "anotherpass1",
            "confirm_password": "different11",
        }, follow_redirects=False)
        check("Несовпадающее подтверждение → ошибка",
              r.status_code not in (301, 302, 303, 307, 308),
              f"status={r.status_code}")

        # 5.6 Новый == текущий
        r = c5b.post("/ru/profile/change-password", data={
            "current_password": "newpass123",
            "new_password": "newpass123",
            "confirm_password": "newpass123",
        }, follow_redirects=False)
        check("Новый = текущий → ошибка/предупреждение",
              r.status_code not in (301, 302, 303, 307, 308),
              f"status={r.status_code}")

        # ============================================================
        # 6. Настройки
        # ============================================================
        print()
        print("--- 6. Настройки ---")
        u6 = make_user(db, User, UserSettings,
                       "set6", "set6@test.com", "pass1234")
        c6 = login_client(app, "set6@test.com", "pass1234")

        r = c6.get("/ru/profile/settings")
        check("/profile/settings GET → 200", r.status_code == 200,
              f"status={r.status_code}")
        s_html = r.data.decode("utf-8")
        check("settings содержит toggle для тёмной темы",
              "dark_mode" in s_html and "checkbox" in s_html.lower())
        check("settings содержит toggle для уведомлений",
              "notifications_enabled" in s_html)

        # POST: dark=on, notifications выключены, lang=en, reminder=21:30
        r = c6.post("/ru/profile/settings", data={
            "dark_mode": "on",
            "language": "en",
            "daily_reminder_time": "21:30",
            # notifications_enabled намеренно не отправляем — должен стать False
        }, follow_redirects=False)
        check("POST /profile/settings → редирект (сохранено)",
              r.status_code in (301, 302, 303, 307, 308),
              f"status={r.status_code}")

        s_db = db.session.execute(
            sa.select(UserSettings).where(UserSettings.user_id == u6.id)
        ).scalar_one()
        check("dark_mode == True в БД", s_db.dark_mode is True,
              f"got={s_db.dark_mode}")
        check("notifications_enabled == False в БД",
              s_db.notifications_enabled is False,
              f"got={s_db.notifications_enabled}")
        check("language == 'en' в БД", s_db.language == "en",
              f"got={s_db.language!r}")
        check("daily_reminder_time == '21:30' в БД",
              s_db.daily_reminder_time == "21:30",
              f"got={s_db.daily_reminder_time!r}")

        # GET после сохранения — форма содержит сохранённые значения
        r = c6.get("/ru/profile/settings")
        s_html2 = r.data.decode("utf-8")
        check("GET после сохранения: dark_mode checkbox с checked",
              re.search(r'name="dark_mode"[^>]*checked|checked[^>]*name="dark_mode"',
                        s_html2) is not None)
        check("GET после сохранения: time = '21:30'", "21:30" in s_html2)
        check("GET после сохранения: language 'en' выбран",
              re.search(r'value="en"[^>]*selected|selected[^>]*value="en"',
                        s_html2) is not None)

        # ============================================================
        # 7. Экспорт данных
        # ============================================================
        print()
        print("--- 7. Экспорт данных ---")
        # JSON
        r = c3.post("/ru/profile/export", data={"format": "json"})
        check("POST /profile/export format=json → 200", r.status_code == 200,
              f"status={r.status_code}")
        ct = r.content_type or ""
        check(
            "Content-Type для JSON содержит 'json' или 'octet-stream'",
            "json" in ct or "octet-stream" in ct,
            f"ct={ct}",
        )
        try:
            payload = json.loads(r.data.decode("utf-8"))
            json_ok = isinstance(payload, dict)
        except Exception as e:
            payload = None; json_ok = False
        check("JSON-экспорт парсится", json_ok)
        if json_ok:
            check("JSON содержит ключ 'entries'", "entries" in payload)
            check("JSON содержит ключ 'tasks'", "tasks" in payload)
            check("JSON содержит данные пользователя (alice8)",
                  payload.get("user", {}).get("email") == "alice8@test.com")

        # PDF (HTML-страница для печати)
        r = c3.post("/ru/profile/export", data={"format": "pdf"})
        check("POST /profile/export format=pdf → 200", r.status_code == 200,
              f"status={r.status_code}")
        ct = r.content_type or ""
        check(
            "Content-Type для pdf — HTML или application/pdf",
            "html" in ct or "pdf" in ct,
            f"ct={ct}",
        )
        body = r.data.decode("utf-8", errors="replace")
        check("Экспорт содержит статистику (XP)",
              "XP" in body or "Уровень" in body or "Streak" in body)

        # 7.x Изоляция: экспорт A не содержит запись B
        u_other = make_user(db, User, UserSettings,
                            "other8", "other8@test.com", "pass1234")
        db.session.add(DailyEntry(
            user_id=u_other.id, date=today,
            anxiety_level=9, text="OTHER_USER_PRIVATE_TEXT",
        ))
        db.session.commit()
        r = c3.post("/ru/profile/export", data={"format": "json"})
        body = r.data.decode("utf-8")
        check("JSON-экспорт A не содержит данные B",
              "OTHER_USER_PRIVATE_TEXT" not in body)

        # ============================================================
        # 8. Удаление аккаунта
        # ============================================================
        print()
        print("--- 8. Удаление аккаунта ---")
        u_del = make_user(db, User, UserSettings,
                          "del8", "del8@test.com", "delpass1")
        u_del_id = u_del.id
        db.session.add(DailyEntry(
            user_id=u_del_id, date=today, anxiety_level=4, text="del-entry",
        ))
        t_del = Task(title="dT", description="d", category="breathing",
                     difficulty="easy", xp_reward=10)
        db.session.add(t_del); db.session.commit()
        db.session.add(UserTask(
            user_id=u_del_id, task_id=t_del.id, completed=True,
            completed_at=datetime.now(timezone.utc),
        ))
        ach = Achievement(name="A1", description="d", icon="🥇",
                          condition_type="tasks_completed", condition_value=1)
        db.session.add(ach); db.session.commit()
        db.session.add(UserAchievement(user_id=u_del_id, achievement_id=ach.id))
        db.session.commit()

        c_del = login_client(app, "del8@test.com", "delpass1")

        # 8.1 Без подтверждения — пусто
        r = c_del.post("/ru/profile/delete-account", data={
            "password": "delpass1",
        }, follow_redirects=False)
        check("Удаление БЕЗ confirmation → не редирект (ошибка)",
              r.status_code not in (301, 302, 303, 307, 308),
              f"status={r.status_code}")
        still = db.session.execute(
            sa.select(User).where(User.id == u_del_id)
        ).scalar_one_or_none()
        check("После запроса без confirmation — аккаунт НЕ удалён",
              still is not None)

        # 8.2 С неверным текстом
        r = c_del.post("/ru/profile/delete-account", data={
            "password": "delpass1",
            "confirmation": "удалить",  # маленькими буквами
        }, follow_redirects=False)
        check("Удаление с неверным текстом → ошибка",
              r.status_code not in (301, 302, 303, 307, 308),
              f"status={r.status_code}")
        still = db.session.execute(
            sa.select(User).where(User.id == u_del_id)
        ).scalar_one_or_none()
        check("После неверного текста — аккаунт НЕ удалён",
              still is not None)

        # 8.3 Корректное удаление
        r = c_del.post("/ru/profile/delete-account", data={
            "password": "delpass1",
            "confirmation": "УДАЛИТЬ",
        }, follow_redirects=False)
        check("Удаление с password+'УДАЛИТЬ' → редирект (успех)",
              r.status_code in (301, 302, 303, 307, 308),
              f"status={r.status_code}")

        gone = db.session.get(User, u_del_id)
        check("User удалён (db.session.get → None)", gone is None,
              f"got={gone}")
        n_entries = db.session.scalar(sa.select(sa.func.count(DailyEntry.id))
                                      .where(DailyEntry.user_id == u_del_id))
        check("DailyEntry для удалённого пользователя → 0",
              n_entries == 0, f"got={n_entries}")
        n_tasks = db.session.scalar(sa.select(sa.func.count(UserTask.id))
                                    .where(UserTask.user_id == u_del_id))
        check("UserTask для удалённого пользователя → 0",
              n_tasks == 0, f"got={n_tasks}")
        n_ua = db.session.scalar(sa.select(sa.func.count(UserAchievement.id))
                                 .where(UserAchievement.user_id == u_del_id))
        check("UserAchievement для удалённого → 0", n_ua == 0,
              f"got={n_ua}")
        n_us = db.session.scalar(sa.select(sa.func.count(UserSettings.id))
                                 .where(UserSettings.user_id == u_del_id))
        check("UserSettings для удалённого → 0", n_us == 0,
              f"got={n_us}")

        # ============================================================
        # 9. Изоляция данных
        # ============================================================
        print()
        print("--- 9. Изоляция данных ---")
        uA = make_user(db, User, UserSettings,
                       "isoA8", "isoA8@test.com", "pass1234")
        uB = make_user(db, User, UserSettings,
                       "isoB8", "isoB8@test.com", "pass1234")
        db.session.add(DailyEntry(user_id=uA.id, date=today,
                                  anxiety_level=2, text="A_TEXT_UNIQUE"))
        db.session.add(DailyEntry(user_id=uB.id, date=today,
                                  anxiety_level=8, text="B_TEXT_UNIQUE"))
        db.session.commit()

        cA = login_client(app, "isoA8@test.com", "pass1234")
        cB = login_client(app, "isoB8@test.com", "pass1234")

        rA = cA.get("/ru/profile/", headers={"Accept": "text/html"})
        rB = cB.get("/ru/profile/", headers={"Accept": "text/html"})
        check("Профиль A не содержит email B",
              "isoB8@test.com" not in rA.data.decode("utf-8"))
        check("Профиль B не содержит email A",
              "isoA8@test.com" not in rB.data.decode("utf-8"))

        expA = cA.post("/ru/profile/export", data={"format": "json"})
        bodyA = expA.data.decode("utf-8")
        check("Экспорт A не содержит запись B (B_TEXT_UNIQUE)",
              "B_TEXT_UNIQUE" not in bodyA)
        check("Экспорт A содержит запись A (A_TEXT_UNIQUE)",
              "A_TEXT_UNIQUE" in bodyA)

        # Удаление A не затрагивает B
        cA.post("/ru/profile/delete-account", data={
            "password": "pass1234",
            "confirmation": "УДАЛИТЬ",
        }, follow_redirects=False)
        b_still = db.session.get(User, uB.id)
        check("Удаление A не затронуло B (B существует)", b_still is not None)
        b_entries = db.session.scalar(sa.select(sa.func.count(DailyEntry.id))
                                      .where(DailyEntry.user_id == uB.id))
        check("Записи B сохранились", b_entries == 1, f"got={b_entries}")

        # ============================================================
        # 10. CSS
        # ============================================================
        print()
        print("--- 10. CSS и тёмная тема ---")
        css = read_file("app/static/css/profile.css")
        css_present = css is not None
        # допускаем inline-стили в HTML
        merged_css = css or ""
        for path in [
            "app/templates/profile/index.html",
            "app/templates/profile/settings.html",
        ]:
            t = read_file(path)
            if t and "<style" in t:
                merged_css += "\n" + t
        check("Файл app/static/css/profile.css существует ИЛИ inline-стили",
              css_present or "<style" in (read_file("app/templates/profile/index.html") or ""))
        check("CSS содержит .dark-theme или .dark-mode",
              ".dark-theme" in merged_css or ".dark-mode" in merged_css
              or "dark-theme" in merged_css or "dark-mode" in merged_css)
        check(
            "CSS содержит стили прогресс-бара",
            "progress-bar" in merged_css or "progress-fill" in merged_css
            or "linear-gradient" in merged_css,
        )
        check("CSS содержит border-radius (скруглённые карточки)",
              "border-radius" in merged_css)
        check(
            "CSS содержит @media (мобильная адаптация)",
            re.search(r"@media\s*\([^)]*(?:max-width|min-width)\s*:", merged_css) is not None,
        )

        # ============================================================
        # 11. UserSettings создаётся автоматически
        # ============================================================
        print()
        print("--- 11. UserSettings авто-создание при регистрации ---")
        reg_client = app.test_client()
        # форма регистрации требует поля
        reg_resp = reg_client.post("/ru/auth/register", data={
            "username": "freshreg",
            "email": "freshreg@test.com",
            "password": "freshpass8",
            "password2": "freshpass8",
            "confirm_password": "freshpass8",  # на случай альтернативного имени
        }, follow_redirects=False)
        # проверим, что пользователь создался (даже если форма требует другие имена)
        u_new = db.session.execute(
            sa.select(User).where(User.email == "freshreg@test.com")
        ).scalar_one_or_none()
        check("Регистрация прошла — пользователь создан",
              u_new is not None,
              f"reg_status={reg_resp.status_code}")

        if u_new is not None:
            s_new = db.session.execute(
                sa.select(UserSettings).where(UserSettings.user_id == u_new.id)
            ).scalar_one_or_none()
            check("UserSettings авто-создан при регистрации",
                  s_new is not None)
            if s_new is not None:
                check("Дефолт: dark_mode == False",
                      s_new.dark_mode is False, f"got={s_new.dark_mode}")
                check("Дефолт: notifications_enabled == True",
                      s_new.notifications_enabled is True,
                      f"got={s_new.notifications_enabled}")
                check("Дефолт: language == 'ru'",
                      s_new.language == "ru", f"got={s_new.language!r}")
                check(
                    "Дефолт: daily_reminder_time == None или '20:00'",
                    s_new.daily_reminder_time in (None, "20:00"),
                    f"got={s_new.daily_reminder_time!r}",
                )

    # ============================================================
    # Итог
    # ============================================================
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
    sys.exit(0 if success else 1)
