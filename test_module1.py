"""
test_module1.py — проверка работоспособности первого модуля SocialHealth.
Запуск: python test_module1.py
"""

import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import traceback

results = []


def check(description, condition, error_msg=""):
    """Записать результат проверки."""
    if condition:
        results.append((True, description, None))
    else:
        results.append((False, description, error_msg))


def run_checks():
    passed = 0
    failed = 0

    print("=" * 60)
    print("SocialHealth — Module 1 Test Suite")
    print("=" * 60)
    print()

    # ============================================================
    # 1. Проверка конфигурации
    # ============================================================
    print("--- 1. Конфигурация ---")

    try:
        import config

        check("Импорт config.py без ошибок", True)
    except Exception as e:
        check("Импорт config.py без ошибок", False, str(e))

    try:
        check(
            "DevelopmentConfig использует SQLite",
            "sqlite" in config.DevelopmentConfig.SQLALCHEMY_DATABASE_URI.lower(),
            f"URI: {config.DevelopmentConfig.SQLALCHEMY_DATABASE_URI}",
        )
    except Exception as e:
        check("DevelopmentConfig использует SQLite", False, str(e))

    try:
        check(
            "ProductionConfig существует",
            hasattr(config, "ProductionConfig"),
        )
    except Exception as e:
        check("ProductionConfig существует", False, str(e))

    try:
        check(
            "TestingConfig использует SQLite in-memory",
            config.TestingConfig.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:",
            f"URI: {config.TestingConfig.SQLALCHEMY_DATABASE_URI}",
        )
    except Exception as e:
        check("TestingConfig использует SQLite in-memory", False, str(e))

    try:
        check(
            "XP_LEVELS содержит 10 уровней",
            len(config.BaseConfig.XP_LEVELS) == 10,
            f"Длина: {len(config.BaseConfig.XP_LEVELS)}",
        )
    except Exception as e:
        check("XP_LEVELS содержит 10 уровней", False, str(e))

    try:
        check(
            "LEVEL_TITLES содержит 10 названий",
            len(config.BaseConfig.LEVEL_TITLES) == 10,
            f"Длина: {len(config.BaseConfig.LEVEL_TITLES)}",
        )
    except Exception as e:
        check("LEVEL_TITLES содержит 10 названий", False, str(e))

    print()

    # ============================================================
    # 2. Проверка Application Factory
    # ============================================================
    print("--- 2. Application Factory ---")

    app = None
    try:
        from app import create_app

        app = create_app()
        check("create_app() создаёт приложение без ошибок", app is not None)
    except Exception as e:
        check("create_app() создаёт приложение без ошибок", False, str(e))

    try:
        test_app = create_app("testing")
        check(
            'create_app("testing") работает с тестовым конфигом',
            test_app is not None and test_app.config.get("TESTING") is True,
        )
    except Exception as e:
        check(
            'create_app("testing") работает с тестовым конфигом',
            False,
            str(e),
        )

    expected_blueprints = [
        "auth",
        "diary",
        "tasks",
        "dashboard",
        "progress",
        "sos",
        "profile",
        "tips",
        "api",
    ]
    if app:
        for bp_name in expected_blueprints:
            try:
                check(
                    f"Blueprint '{bp_name}' зарегистрирован",
                    bp_name in app.blueprints,
                    f"Зарегистрированы: {list(app.blueprints.keys())}",
                )
            except Exception as e:
                check(
                    f"Blueprint '{bp_name}' зарегистрирован", False, str(e)
                )
    else:
        for bp_name in expected_blueprints:
            check(
                f"Blueprint '{bp_name}' зарегистрирован",
                False,
                "Приложение не создано",
            )

    print()

    # ============================================================
    # 3. Проверка Extensions
    # ============================================================
    print("--- 3. Extensions ---")

    try:
        from app.extensions import db

        check("db (SQLAlchemy) импортируется", True)
    except Exception as e:
        check("db (SQLAlchemy) импортируется", False, str(e))

    try:
        from app.extensions import jwt

        check("jwt (JWTManager) импортируется", True)
    except Exception as e:
        check("jwt (JWTManager) импортируется", False, str(e))

    try:
        from app.extensions import migrate

        check("migrate (Migrate) импортируется", True)
    except Exception as e:
        check("migrate (Migrate) импортируется", False, str(e))

    try:
        from app.extensions import limiter

        check("limiter (Limiter) импортируется", True)
    except Exception as e:
        check("limiter (Limiter) импортируется", False, str(e))

    try:
        from app.extensions import csrf

        check("csrf (CSRFProtect) импортируется", True)
    except Exception as e:
        check("csrf (CSRFProtect) импортируется", False, str(e))

    print()

    # ============================================================
    # 4. Проверка моделей
    # ============================================================
    print("--- 4. Модели ---")

    models_ok = True
    try:
        from app.models import (
            User,
            DailyEntry,
            Task,
            UserTask,
            Achievement,
            UserAchievement,
            UserSettings,
        )

        check("Все модели импортируются", True)
    except Exception as e:
        check("Все модели импортируются", False, str(e))
        models_ok = False

    if models_ok:
        test_app = create_app("testing")
        with test_app.app_context():
            try:
                db.create_all()
                check("Создание таблиц в тестовой БД (db.create_all)", True)
            except Exception as e:
                check("Создание таблиц в тестовой БД (db.create_all)", False, str(e))

            # --- User ---
            try:
                user = User(email="test@example.com", username="testuser")
                user.set_password("secret123")
                db.session.add(user)
                db.session.commit()
                check("User.set_password() работает", True)
            except Exception as e:
                check("User.set_password() работает", False, str(e))

            try:
                ok = user.check_password("secret123")
                check("User.check_password() с верным паролем", ok)
            except Exception as e:
                check("User.check_password() с верным паролем", False, str(e))

            try:
                ok = not user.check_password("wrongpass")
                check("User.check_password() с неверным паролем", ok)
            except Exception as e:
                check("User.check_password() с неверным паролем", False, str(e))

            try:
                leveled_up = user.add_xp(150)
                db.session.commit()
                check(
                    "User.add_xp(150) повышает уровень до 2",
                    leveled_up and user.level == 2,
                    f"level={user.level}, leveled_up={leveled_up}",
                )
            except Exception as e:
                check("User.add_xp(150) повышает уровень до 2", False, str(e))

            try:
                # Сбросим user для чистоты
                user2 = User(email="test2@example.com", username="testuser2")
                user2.set_password("pass")
                db.session.add(user2)
                db.session.commit()
                user2.add_xp(5000)
                db.session.commit()
                check(
                    "User.add_xp(5000) даёт максимальный уровень 10",
                    user2.level == 10,
                    f"level={user2.level}",
                )
            except Exception as e:
                check("User.add_xp(5000) даёт максимальный уровень 10", False, str(e))

            # --- DailyEntry ---
            try:
                from datetime import date

                entry = DailyEntry(
                    user_id=user.id,
                    date=date.today(),
                    anxiety_level=7,
                    emotions={"joy": 0.3, "fear": 0.7},
                    text="Сегодня было трудно, но я справился.",
                )
                db.session.add(entry)
                db.session.commit()
                check(
                    "Создание DailyEntry с anxiety_level=7, emotions, text",
                    entry.id is not None,
                )
            except Exception as e:
                check(
                    "Создание DailyEntry с anxiety_level=7, emotions, text",
                    False,
                    str(e),
                )

            try:
                check(
                    "Связь User → DailyEntry через relationship",
                    len(user.entries) >= 1 and user.entries[0].id == entry.id,
                )
            except Exception as e:
                check("Связь User → DailyEntry через relationship", False, str(e))

            # --- Task ---
            try:
                task = Task(
                    title="Сделать звонок другу",
                    description="Позвонить другу и поговорить 5 минут",
                    difficulty="easy",
                    xp_reward=15,
                    category="communication",
                    min_anxiety=1,
                    max_anxiety=5,
                )
                db.session.add(task)
                db.session.commit()
                check(
                    'Создание Task с difficulty="easy", xp_reward=15',
                    task.id is not None,
                )
            except Exception as e:
                check(
                    'Создание Task с difficulty="easy", xp_reward=15',
                    False,
                    str(e),
                )

            # --- UserTask ---
            try:
                user_task = UserTask(
                    user_id=user.id,
                    task_id=task.id,
                    completed=False,
                )
                db.session.add(user_task)
                db.session.commit()
                user_task.completed = True
                from datetime import datetime, timezone

                user_task.completed_at = datetime.now(timezone.utc)
                db.session.commit()
                check(
                    "Создание UserTask и отметка completed=True",
                    user_task.completed is True,
                )
            except Exception as e:
                check("Создание UserTask и отметка completed=True", False, str(e))

            # --- Achievement ---
            try:
                achievement = Achievement(
                    name="Недельный марафон",
                    description="7 дней подряд",
                    icon="🔥",
                    condition_type="streak",
                    condition_value=7,
                )
                db.session.add(achievement)
                db.session.commit()
                check(
                    'Создание Achievement с condition_type="streak", condition_value=7',
                    achievement.id is not None,
                )
            except Exception as e:
                check(
                    'Создание Achievement с condition_type="streak", condition_value=7',
                    False,
                    str(e),
                )

            # --- UserAchievement ---
            try:
                ua = UserAchievement(
                    user_id=user.id,
                    achievement_id=achievement.id,
                )
                db.session.add(ua)
                db.session.commit()
                check("Создание UserAchievement", ua.id is not None)
            except Exception as e:
                check("Создание UserAchievement", False, str(e))

            try:
                from sqlalchemy.exc import IntegrityError

                ua_dup = UserAchievement(
                    user_id=user.id,
                    achievement_id=achievement.id,
                )
                db.session.add(ua_dup)
                db.session.commit()
                check(
                    "UserAchievement UniqueConstraint работает",
                    False,
                    "Дубликат был создан без ошибки",
                )
            except IntegrityError:
                db.session.rollback()
                check("UserAchievement UniqueConstraint работает", True)
            except Exception as e:
                db.session.rollback()
                check("UserAchievement UniqueConstraint работает", False, str(e))

            # --- UserSettings ---
            try:
                settings = UserSettings(
                    user_id=user.id,
                    dark_mode=True,
                    notifications_enabled=False,
                    language="en",
                    daily_reminder_time="09:00",
                )
                db.session.add(settings)
                db.session.commit()
                check(
                    "Создание UserSettings с dark_mode=True",
                    settings.id is not None and settings.dark_mode is True,
                )
            except Exception as e:
                check("Создание UserSettings с dark_mode=True", False, str(e))

            # --- Индексы ---
            try:
                from sqlalchemy import inspect as sa_inspect

                inspector = sa_inspect(db.engine)
                daily_entry_indexes = inspector.get_indexes("daily_entries")
                index_names = [idx["name"] for idx in daily_entry_indexes]
                check(
                    "Индекс на DailyEntry (user_id, date)",
                    "ix_daily_entries_user_id_date" in index_names,
                    f"Индексы: {index_names}",
                )
            except Exception as e:
                check("Индекс на DailyEntry (user_id, date)", False, str(e))

            try:
                user_task_indexes = inspector.get_indexes("user_tasks")
                index_names = [idx["name"] for idx in user_task_indexes]
                check(
                    "Индекс на UserTask (user_id, completed_at)",
                    "ix_user_tasks_user_id_completed_at" in index_names,
                    f"Индексы: {index_names}",
                )
            except Exception as e:
                check("Индекс на UserTask (user_id, completed_at)", False, str(e))

    print()

    # ============================================================
    # 5. Проверка связей между моделями
    # ============================================================
    print("--- 5. Связи между моделями ---")

    if models_ok:
        test_app = create_app("testing")
        with test_app.app_context():
            db.create_all()

            try:
                u = User(email="rel@example.com", username="reluser")
                u.set_password("pass")
                db.session.add(u)
                db.session.commit()

                e = DailyEntry(
                    user_id=u.id,
                    date=date.today(),
                    anxiety_level=5,
                )
                db.session.add(e)

                t = Task(
                    title="Тестовая задача",
                    difficulty="medium",
                    xp_reward=20,
                    category="test",
                )
                db.session.add(t)
                db.session.commit()

                ut = UserTask(user_id=u.id, task_id=t.id)
                db.session.add(ut)
                db.session.commit()

                a = Achievement(
                    name="Тест ачивки",
                    icon="🧪",
                    condition_type="xp_earned",
                    condition_value=100,
                )
                db.session.add(a)
                db.session.commit()

                ua = UserAchievement(user_id=u.id, achievement_id=a.id)
                db.session.add(ua)

                us = UserSettings(user_id=u.id, dark_mode=True)
                db.session.add(us)
                db.session.commit()

                check(
                    "User.entries возвращает список DailyEntry",
                    isinstance(u.entries, list) and len(u.entries) == 1,
                )
            except Exception as e:
                check("User.entries возвращает список DailyEntry", False, str(e))

            try:
                check(
                    "User.user_tasks возвращает список UserTask",
                    isinstance(u.user_tasks, list) and len(u.user_tasks) == 1,
                )
            except Exception as e:
                check("User.user_tasks возвращает список UserTask", False, str(e))

            try:
                check(
                    "User.achievements возвращает список UserAchievement",
                    isinstance(u.achievements, list) and len(u.achievements) == 1,
                )
            except Exception as e:
                check(
                    "User.achievements возвращает список UserAchievement",
                    False,
                    str(e),
                )

            try:
                check(
                    "User.settings возвращает UserSettings",
                    u.settings is not None and u.settings.dark_mode is True,
                )
            except Exception as e:
                check("User.settings возвращает UserSettings", False, str(e))

            try:
                check(
                    "UserTask.task возвращает связанный Task",
                    ut.task is not None and ut.task.id == t.id,
                )
            except Exception as e:
                check("UserTask.task возвращает связанный Task", False, str(e))

            try:
                check(
                    "UserTask.user возвращает связанного User",
                    ut.user is not None and ut.user.id == u.id,
                )
            except Exception as e:
                check("UserTask.user возвращает связанного User", False, str(e))

    print()

    # ============================================================
    # Итоги
    # ============================================================
    for ok, desc, err in results:
        if ok:
            print(f"[OK] {desc}")
            passed += 1
        else:
            print(f"[FAIL] {desc} — ошибка: {err}")
            failed += 1

    total = passed + failed
    print()
    print("=" * 60)
    print(f"Пройдено {passed} из {total} тестов")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_checks()
    exit(0 if success else 1)
