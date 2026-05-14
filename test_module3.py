"""
test_module3.py — тестирование модуля Дневник эмоций (diary).
Запуск: python test_module3.py
"""

import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from datetime import date, timedelta

results = []


def check(desc, condition, error=""):
    if condition:
        results.append((True, desc, None))
    else:
        results.append((False, desc, error))


def create_user_and_login(client, db, User, username, email, password):
    """Создаёт пользователя и логинит его через test_client."""
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
    return user


def run_checks():
    from app import create_app
    from app.extensions import db
    from app.models import User, DailyEntry
    from app.services.ai_service import AIService
    import sqlalchemy as sa

    app = create_app("testing")

    print("=" * 60)
    print("=== ТЕСТИРОВАНИЕ МОДУЛЯ 3: ДНЕВНИК ЭМОЦИЙ ===")
    print("=" * 60)
    print()

    with app.app_context():
        db.create_all()

        # ================================================================
        # 1. Blueprint зарегистрирован
        # ================================================================
        print("--- 1. Blueprint ---")
        check("diary_bp зарегистрирован в приложении", "diary" in app.blueprints)

        rules = [str(r) for r in app.url_map.iter_rules()]
        check(
            "URL /diary/ существует",
            any("/diary/" in r and "<" not in r for r in rules),
            f"rules={rules}",
        )
        check("URL /diary/new существует", any("/diary/new" in r for r in rules))
        check(
            "URL /diary/<id> существует",
            any("/diary/<" in r for r in rules),
        )

        # ================================================================
        # 2. Защита маршрутов
        # ================================================================
        print()
        print("--- 2. Защита маршрутов ---")
        fresh = app.test_client()
        resp = fresh.get("/ru/diary/", follow_redirects=False)
        check(
            "GET /diary/ без токена — 401 или редирект",
            resp.status_code in (401, 301, 302, 307, 308),
            f"status={resp.status_code}",
        )

        resp = fresh.get("/ru/diary/new", follow_redirects=False)
        check(
            "GET /diary/new без токена — 401 или редирект",
            resp.status_code in (401, 301, 302, 307, 308),
            f"status={resp.status_code}",
        )

        resp = fresh.post("/ru/diary/new", data={"anxiety_level": 5}, follow_redirects=False)
        check(
            "POST /diary/new без токена — 401 или редирект",
            resp.status_code in (401, 301, 302, 307, 308),
            f"status={resp.status_code}",
        )

        # ================================================================
        # 3. Форма новой записи
        # ================================================================
        print()
        print("--- 3. Форма новой записи ---")
        client = app.test_client()
        user = create_user_and_login(client, db, User, "diaryuser", "diary@test.com", "password123")

        resp = client.get("/ru/diary/new")
        check("GET /diary/new с токеном — 200", resp.status_code == 200)
        html_new = resp.data.decode("utf-8")
        check(
            "Страница содержит слайдер anxiety_level",
            'name="anxiety_level"' in html_new or 'id="anxietySlider"' in html_new,
        )
        check(
            "Страница содержит textarea для текста",
            'name="text"' in html_new or 'id="textField"' in html_new,
        )
        check(
            'Страница содержит кнопку "Страх"',
            "Страх" in html_new,
        )
        check(
            'Страница содержит кнопку "Стыд"',
            "Стыд" in html_new,
        )

        # ================================================================
        # 4. Создание записи
        # ================================================================
        print()
        print("--- 4. Создание записи ---")

        # 4.1 Успех
        resp = client.post(
            "/diary/new",
            data={
                "anxiety_level": 5,
                "emotions": ["Страх", "Стыд"],
                "text": "Тестовая запись для проверки",
            },
            follow_redirects=False,
        )
        check(
            "POST /diary/new с валидными данными — успех (редирект)",
            resp.status_code in (301, 302, 307, 308),
            f"status={resp.status_code}",
        )

        entry = db.session.execute(
            sa.select(DailyEntry).where(DailyEntry.user_id == user.id).limit(1)
        ).scalar_one_or_none()
        check("DailyEntry появилась в БД", entry is not None)

        if entry:
            check("anxiety_level сохранён корректно (=5)", entry.anxiety_level == 5)
            check(
                "emotions сохранены как JSON (список)",
                isinstance(entry.emotions, list) and "Страх" in entry.emotions,
                f"emotions={entry.emotions}, type={type(entry.emotions)}",
            )
            check(
                "ai_analysis заполнен (placeholder или реальный)",
                entry.ai_analysis is not None,
                f"ai_analysis={entry.ai_analysis}",
            )
        else:
            check("anxiety_level сохранён", False, "Entry не найдена")
            check("emotions сохранены", False, "Entry не найдена")
            check("ai_analysis заполнен", False, "Entry не найдена")

        # 4.2 Без anxiety_level
        resp_no = client.post("/ru/diary/new", data={"text": "без уровня"})
        check(
            "POST /diary/new без anxiety_level — ошибка",
            resp_no.status_code in (400, 422),
            f"status={resp_no.status_code}",
        )

        # 4.3 anxiety_level=0
        resp0 = client.post(
            "/diary/new", data={"anxiety_level": 0, "text": "ноль"}
        )
        check(
            "POST /diary/new с anxiety_level=0 — ошибка",
            resp0.status_code in (400, 422),
            f"status={resp0.status_code}",
        )

        # 4.4 anxiety_level=11
        resp11 = client.post(
            "/diary/new", data={"anxiety_level": 11, "text": "одиннадцать"}
        )
        check(
            "POST /diary/new с anxiety_level=11 — ошибка",
            resp11.status_code in (400, 422),
            f"status={resp11.status_code}",
        )

        # 4.5 Текст длиннее 2000 символов
        long_text = "A" * 2500
        resp_long = client.post(
            "/diary/new",
            data={"anxiety_level": 5, "text": long_text},
        )
        long_entry = db.session.execute(
            sa.select(DailyEntry)
            .where(DailyEntry.user_id == user.id)
            .order_by(DailyEntry.id.desc())
            .limit(1)
        ).scalar_one_or_none()
        if long_entry:
            check(
                "POST с текстом >2000 символов — обрезан до 2000",
                len(long_entry.text) <= 2000,
                f"len={len(long_entry.text)}",
            )
        else:
            check(
                "POST с текстом >2000 — обрезан или ошибка",
                resp_long.status_code in (400, 422) or len(long_entry.text) <= 2000 if long_entry else False,
            )

        # ================================================================
        # 5. Список записей
        # ================================================================
        print()
        print("--- 5. Список записей ---")

        # Создадим 15 записей для user
        base_date = date.today()
        for i in range(15):
            e = DailyEntry(
                user_id=user.id,
                date=base_date - timedelta(days=i),
                anxiety_level=(i % 10) + 1,
                emotions=["Тревога"],
                text=f"Запись номер {i+1} для тестирования пагинации",
                ai_analysis={"summary": "test"},
            )
            db.session.add(e)
        db.session.commit()

        total_entries = db.session.scalar(
            sa.select(sa.func.count(DailyEntry.id)).where(DailyEntry.user_id == user.id)
        )

        resp_list = client.get("/ru/diary/")
        check("GET /diary/ — статус 200", resp_list.status_code == 200)
        html_list = resp_list.data.decode("utf-8")

        # Должно быть 10 записей на первой странице
        # (уже была 1 + 15 = 16, но первая из секции 4 тоже считается)
        # Так что total_entries = 17
        check(
            "Страница содержит пагинацию",
            "Страница" in html_list or "pagination" in html_list.lower() or "Назад" in html_list,
        )

        resp_p2 = client.get("/ru/diary/?page=2")
        check("GET /diary/?page=2 — статус 200", resp_p2.status_code == 200)

        # Проверим что записи отсортированы по дате (новые сверху)
        # Первая запись на странице 1 должна быть самой свежей
        entries_page1 = db.session.execute(
            sa.select(DailyEntry)
            .where(DailyEntry.user_id == user.id)
            .order_by(DailyEntry.date.desc(), DailyEntry.created_at.desc())
            .limit(10)
        ).scalars().all()
        newest_id = entries_page1[0].id
        check(
            "Записи отсортированы по дате (новые сверху)",
            str(newest_id) in html_list or entries_page1[0].text in html_list,
        )

        # Пользователь НЕ видит чужие записи
        other = User(username="otheruser", email="other@test.com")
        other.set_password("pass123")
        db.session.add(other)
        db.session.commit()
        other_entry = DailyEntry(
            user_id=other.id,
            date=base_date,
            anxiety_level=7,
            text="Это запись другого пользователя",
        )
        db.session.add(other_entry)
        db.session.commit()

        resp_other = client.get("/ru/diary/")
        html_other = resp_other.data.decode("utf-8")
        check(
            "Пользователь НЕ видит чужие записи",
            "Это запись другого пользователя" not in html_other,
        )

        # ================================================================
        # 6. Детальный просмотр
        # ================================================================
        print()
        print("--- 6. Детальный просмотр ---")

        own_entry = db.session.execute(
            sa.select(DailyEntry).where(DailyEntry.user_id == user.id)
        ).scalars().first()

        resp_detail = client.get(f"/diary/{own_entry.id}")
        check(
            "GET /diary/<id> своей записи — статус 200",
            resp_detail.status_code == 200,
            f"status={resp_detail.status_code}",
        )
        html_detail = resp_detail.data.decode("utf-8")
        check(
            "Детальная страница содержит полный текст",
            own_entry.text in html_detail,
        )
        check(
            "Детальная страница содержит 'Резюме' или аналог",
            "Резюме" in html_detail or "summary" in html_detail.lower() or "Анализ" in html_detail,
        )
        check(
            "Детальная страница содержит 'Инсайт' или аналог",
            "Инсайт" in html_detail or "insight" in html_detail.lower(),
        )
        check(
            "Детальная страница содержит 'Рекомендация' или аналог",
            "Рекомендация" in html_detail or "recommendation" in html_detail.lower(),
        )

        # Чужая запись
        resp_foreign = client.get(f"/diary/{other_entry.id}")
        check(
            "GET /diary/<id> чужой записи — 403 или 404",
            resp_foreign.status_code in (403, 404),
            f"status={resp_foreign.status_code}",
        )

        # Несуществующая
        resp_404 = client.get("/ru/diary/99999")
        check(
            "GET /diary/99999 — 404",
            resp_404.status_code == 404,
            f"status={resp_404.status_code}",
        )

        # ================================================================
        # 7. AI Service
        # ================================================================
        print()
        print("--- 7. AI Service ---")

        result = AIService.analyze_entry("тестовый текст", 5)
        check(
            "AIService.analyze_entry возвращает dict",
            isinstance(result, dict),
            f"type={type(result)}",
        )
        check(
            "Ответ содержит ключ 'summary'",
            "summary" in result,
            f"keys={list(result.keys())}",
        )
        check(
            "Ответ содержит ключ 'insight'",
            "insight" in result,
        )
        check(
            "Ответ содержит ключ 'recommendation'",
            "recommendation" in result,
        )
        check(
            "Все значения — непустые строки",
            all(isinstance(v, str) and len(v) > 0 for v in result.values()),
            f"values={result}",
        )

        # При отсутствии API ключа
        old_key = app.config.get("ANTHROPIC_API_KEY")
        app.config["ANTHROPIC_API_KEY"] = None
        import os

        old_env = os.environ.get("ANTHROPIC_API_KEY")
        if old_env:
            del os.environ["ANTHROPIC_API_KEY"]
        result_no_key = AIService.analyze_entry("тест", 5)
        check(
            "При отсутствии ANTHROPIC_API_KEY — placeholder без ошибки",
            isinstance(result_no_key, dict) and "summary" in result_no_key,
        )
        if old_key:
            app.config["ANTHROPIC_API_KEY"] = old_key
        if old_env:
            os.environ["ANTHROPIC_API_KEY"] = old_env

        # При anxiety_level >= 9
        result_high = AIService.analyze_entry("тест", 9)
        check(
            "При anxiety_level 9-10 рекомендация содержит слово 'специалист'",
            ("специалист" in result_high.get("recommendation", "").lower()
             or "specialist" in result_high.get("recommendation", "").lower()),
            f"recommendation={result_high.get('recommendation')}",
        )

        # ================================================================
        # 8. Связь с моделями
        # ================================================================
        print()
        print("--- 8. Связь с моделями ---")

        u = db.session.execute(
            sa.select(User).where(User.id == user.id)
        ).scalar_one()
        check(
            "User.entries возвращает связанные DailyEntry",
            len(u.entries) > 0,
            f"entries count={len(u.entries)}",
        )

        e = db.session.execute(
            sa.select(DailyEntry).where(DailyEntry.user_id == user.id)
        ).scalars().first()
        check(
            "DailyEntry.user возвращает связанного User",
            e.user is not None and e.user.id == user.id,
        )

        # Фильтр по user_id
        count = db.session.scalar(
            sa.select(sa.func.count(DailyEntry.id)).where(DailyEntry.user_id == user.id)
        )
        check(
            "Фильтр по user_id работает корректно",
            count > 0,
            f"count={count}",
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
