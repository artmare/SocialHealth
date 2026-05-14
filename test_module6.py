"""
test_module6.py — тестирование модуля 6 (дашборд, прогресс, API статистики).
Запуск: python test_module6.py
"""

import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from datetime import date, datetime, timedelta, timezone
import json

results = []


def check(desc, condition, error=""):
    if condition:
        results.append((True, desc, None))
    else:
        results.append((False, desc, error))


def login_client(app, email, password):
    """Создаёт test_client, логинится, возвращает клиент с JWT-куками."""
    c = app.test_client()
    c.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
    return c


def make_user(db, User, username, email, password, **kw):
    u = User(username=username, email=email, **kw)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return u


def run_checks():
    from app import create_app
    from app.extensions import db
    from app.models import (
        User,
        DailyEntry,
        Task,
        UserTask,
        Achievement,
        UserAchievement,
    )
    from app.services.stats_service import StatsService
    import sqlalchemy as sa

    app = create_app("testing")

    print("=" * 60)
    print("=== ТЕСТИРОВАНИЕ МОДУЛЯ 6: ДАШБОРД И ПРОГРЕСС ===")
    print("=" * 60)
    print()

    with app.app_context():
        db.create_all()

        # ============================================================
        # 1. Blueprints зарегистрированы
        # ============================================================
        print("--- 1. Blueprints и маршруты ---")
        check("Blueprint dashboard зарегистрирован", "dashboard" in app.blueprints)
        check("Blueprint progress зарегистрирован", "progress" in app.blueprints)
        check("Blueprint api зарегистрирован", "api" in app.blueprints)

        rules = {str(r.rule) for r in app.url_map.iter_rules()}
        for url in [
            "/dashboard/",
            "/progress/",
            "/api/stats/anxiety",
            "/api/stats/tasks",
            "/api/stats/summary",
            "/api/stats/comparison",
        ]:
            check(f"URL {url} существует", url in rules, f"rules={sorted(rules)[:5]}…")

        # ============================================================
        # 2. Защита маршрутов (без токена)
        # ============================================================
        print()
        print("--- 2. Защита маршрутов без токена ---")
        anon = app.test_client()
        for url in ["/dashboard/", "/progress/"]:
            r = anon.get(url, follow_redirects=False)
            check(
                f"GET {url} без токена — редирект или 401",
                r.status_code in (401, 301, 302, 307, 308),
                f"status={r.status_code}",
            )
        for url in ["/api/stats/anxiety", "/api/stats/summary",
                    "/api/stats/tasks", "/api/stats/comparison"]:
            r = anon.get(url, follow_redirects=False)
            check(
                f"GET {url} без токена — 401",
                r.status_code == 401,
                f"status={r.status_code}",
            )

        # ============================================================
        # 3. StatsService.get_dashboard_stats
        # ============================================================
        print()
        print("--- 3. StatsService.get_dashboard_stats ---")
        user3 = make_user(
            db, User, "alice3", "alice3@test.com", "pass1234",
            xp=150, level=2, streak=5,
        )
        today = date.today()
        for offset, lvl in enumerate([3, 5, 7]):
            db.session.add(DailyEntry(
                user_id=user3.id,
                date=today - timedelta(days=offset),
                anxiety_level=lvl,
                text="t",
            ))
        t_easy = Task(
            title="T1", description="d", category="breathing",
            difficulty="easy", xp_reward=10,
        )
        t_med = Task(
            title="T2", description="d", category="cognition",
            difficulty="medium", xp_reward=25,
        )
        db.session.add_all([t_easy, t_med])
        db.session.commit()
        for t in (t_easy, t_med):
            db.session.add(UserTask(
                user_id=user3.id, task_id=t.id, completed=True,
                completed_at=datetime.now(timezone.utc),
            ))
        db.session.commit()

        s = StatsService.get_dashboard_stats(user3.id)
        for key in ("streak", "xp", "level", "level_title",
                    "total_tasks_completed", "total_entries",
                    "avg_anxiety", "avg_anxiety_week",
                    "xp_to_next_level", "xp_progress_pct"):
            check(f"get_dashboard_stats содержит ключ '{key}'", key in s,
                  f"keys={list(s.keys())}")

        check("streak == 5", s["streak"] == 5, f"streak={s['streak']}")
        check("xp == 150", s["xp"] == 150, f"xp={s['xp']}")
        check("level == 2", s["level"] == 2, f"level={s['level']}")
        check(
            "level_title — непустая строка",
            isinstance(s["level_title"], str) and len(s["level_title"]) > 0,
            f"level_title={s['level_title']!r}",
        )
        check("total_tasks_completed == 2",
              s["total_tasks_completed"] == 2,
              f"got={s['total_tasks_completed']}")
        check("total_entries == 3", s["total_entries"] == 3,
              f"got={s['total_entries']}")
        check("avg_anxiety == 5.0",
              abs(s["avg_anxiety"] - 5.0) < 0.01,
              f"got={s['avg_anxiety']}")
        # XP_LEVELS: [0,100,250,500,...] => level 2 пороги [100, 250], до сл. = 100
        check("xp_to_next_level == 100",
              s["xp_to_next_level"] == 100,
              f"got={s['xp_to_next_level']}")
        # progress: (150-100)/(250-100)*100 = 33.33%
        check("xp_progress_pct в диапазоне 33–34%",
              33.0 <= s["xp_progress_pct"] <= 34.0,
              f"got={s['xp_progress_pct']}")

        # ============================================================
        # 4. StatsService.get_anxiety_history
        # ============================================================
        print()
        print("--- 4. StatsService.get_anxiety_history ---")
        user4 = make_user(db, User, "bob4", "bob4@test.com", "pass1234")
        for offset, lvl in enumerate([2, 4, 6, 8, 3]):
            db.session.add(DailyEntry(
                user_id=user4.id,
                date=today - timedelta(days=offset),
                anxiety_level=lvl,
                text="x",
            ))
        db.session.commit()

        hist30 = StatsService.get_anxiety_history(user4.id, days=30)
        check("get_anxiety_history(days=30) — список",
              isinstance(hist30, list))
        check("get_anxiety_history(days=30) длина == 5",
              len(hist30) == 5, f"len={len(hist30)}")
        check(
            "Каждый элемент содержит 'date' (строка ISO) и 'anxiety_level' (int)",
            all(
                isinstance(e.get("date"), str)
                and len(e["date"]) == 10
                and isinstance(e.get("anxiety_level"), int)
                for e in hist30
            ),
            f"sample={hist30[:1]}",
        )
        check(
            "История отсортирована по дате (от старых к новым)",
            all(hist30[i]["date"] <= hist30[i + 1]["date"] for i in range(len(hist30) - 1)),
        )

        hist2 = StatsService.get_anxiety_history(user4.id, days=2)
        # за days=2 окно — today и today-1d и today-2d (since = today-2d, включительно)
        check(
            "get_anxiety_history(days=2) возвращает только последние записи (≤3)",
            1 <= len(hist2) <= 3,
            f"len={len(hist2)}",
        )

        # ============================================================
        # 5. StatsService.get_tasks_by_week
        # ============================================================
        print()
        print("--- 5. StatsService.get_tasks_by_week ---")
        user5 = make_user(db, User, "carol5", "carol5@test.com", "pass1234")
        t5 = Task(
            title="T5", description="d", category="breathing",
            difficulty="easy", xp_reward=10,
        )
        db.session.add(t5)
        db.session.commit()

        now = datetime.now(timezone.utc)
        # Текущая неделя — 3 шт.
        this_week_monday_dt = (now - timedelta(days=now.weekday())).replace(
            hour=12, minute=0, second=0, microsecond=0,
        )
        for i in range(3):
            db.session.add(UserTask(
                user_id=user5.id, task_id=t5.id, completed=True,
                completed_at=this_week_monday_dt + timedelta(hours=i),
            ))
        # Прошлая неделя — 2 шт.
        last_week_dt = this_week_monday_dt - timedelta(days=3)
        for i in range(2):
            db.session.add(UserTask(
                user_id=user5.id, task_id=t5.id, completed=True,
                completed_at=last_week_dt + timedelta(hours=i),
            ))
        db.session.commit()

        weekly = StatsService.get_tasks_by_week(user5.id, weeks=8)
        check("get_tasks_by_week — список", isinstance(weekly, list))
        check(
            "Каждый элемент содержит 'week' (ISO) и 'count' (int)",
            all(
                isinstance(e.get("week"), str)
                and len(e["week"]) == 10
                and isinstance(e.get("count"), int)
                for e in weekly
            ),
        )
        non_zero = sorted([e["count"] for e in weekly if e["count"] > 0], reverse=True)
        check(
            "Ровно 2 непустые недели",
            len(non_zero) == 2,
            f"non_zero={non_zero}, all={weekly}",
        )
        check(
            "Одна неделя с count=3, другая с count=2",
            non_zero == [3, 2],
            f"non_zero={non_zero}",
        )

        # ============================================================
        # 6. StatsService.get_anxiety_comparison
        # ============================================================
        print()
        print("--- 6. StatsService.get_anxiety_comparison ---")
        user6 = make_user(db, User, "dave6", "dave6@test.com", "pass1234")
        # Текущая неделя (today и 6 предыдущих дней): anxiety=4 → avg=4.0
        for offset in range(7):
            db.session.add(DailyEntry(
                user_id=user6.id,
                date=today - timedelta(days=offset),
                anxiety_level=4,
                text="cur",
            ))
        # Прошлая неделя (days 7..13): anxiety=6 → avg=6.0
        for offset in range(7, 14):
            db.session.add(DailyEntry(
                user_id=user6.id,
                date=today - timedelta(days=offset),
                anxiety_level=6,
                text="prev",
            ))
        db.session.commit()

        cmp_ = StatsService.get_anxiety_comparison(user6.id)
        for key in ("current_week_avg", "previous_week_avg", "change_pct", "trend"):
            check(f"comparison содержит ключ '{key}'", key in cmp_,
                  f"keys={list(cmp_.keys())}")
        check("current_week_avg ≈ 4.0",
              abs(cmp_["current_week_avg"] - 4.0) < 0.01,
              f"got={cmp_['current_week_avg']}")
        check("previous_week_avg ≈ 6.0",
              abs(cmp_["previous_week_avg"] - 6.0) < 0.01,
              f"got={cmp_['previous_week_avg']}")
        check("change_pct < 0 (улучшение)",
              cmp_["change_pct"] < 0,
              f"got={cmp_['change_pct']}")
        check("trend == 'improving'",
              cmp_["trend"] == "improving",
              f"got={cmp_['trend']}")

        # ============================================================
        # 7. Страница дашборда (GET /dashboard/)
        # ============================================================
        print()
        print("--- 7. Страница дашборда ---")
        # Возьмём user3 (alice3) — у неё есть данные
        c7 = login_client(app, "alice3@test.com", "pass1234")
        r = c7.get("/ru/dashboard/", follow_redirects=False)
        check("GET /dashboard/ с токеном — 200",
              r.status_code == 200, f"status={r.status_code}")
        html = r.data.decode("utf-8")
        check("Дашборд содержит имя пользователя или email",
              "alice3" in html or "alice3@test.com" in html)
        check("Дашборд содержит streak (число 5)", "5" in html)
        check("Дашборд содержит XP", "XP" in html or "xp" in html)
        check(
            "Дашборд содержит 'Задание дня' или аналогичный заголовок",
            "Задание дня" in html or "задание" in html.lower() or "Task of the day" in html or "task of the day" in html.lower(),
        )
        check("Дашборд содержит ссылку на /diary/new", "/diary/new" in html)

        # ============================================================
        # 8. Страница прогресса (GET /progress/)
        # ============================================================
        print()
        print("--- 8. Страница прогресса ---")
        ach1 = Achievement(
            name="Первый шаг", description="Сделай первое задание",
            icon="🥇", condition_type="tasks_completed", condition_value=1,
        )
        ach2 = Achievement(
            name="Неделя", description="Streak 7",
            icon="🔥", condition_type="streak", condition_value=7,
        )
        db.session.add_all([ach1, ach2])
        db.session.commit()
        db.session.add(UserAchievement(user_id=user3.id, achievement_id=ach1.id))
        db.session.commit()

        r = c7.get("/ru/progress/", follow_redirects=False)
        check("GET /progress/ с токеном — 200",
              r.status_code == 200, f"status={r.status_code}")
        html_p = r.data.decode("utf-8")
        check(
            "Страница прогресса содержит 'chart' или 'Chart' (Chart.js подключён)",
            "chart" in html_p.lower(),
        )
        check(
            "Страница прогресса содержит 'Прогресс'",
            "Прогресс" in html_p or "прогресс" in html_p,
        )
        check(
            "Страница прогресса содержит блок достижений",
            "Достижения" in html_p or "достижени" in html_p.lower(),
        )

        # ============================================================
        # 9. API эндпоинты
        # ============================================================
        print()
        print("--- 9. API эндпоинты ---")

        r = c7.get("/ru/api/stats/anxiety")
        check("GET /api/stats/anxiety — 200",
              r.status_code == 200, f"status={r.status_code}")
        check("/api/stats/anxiety — JSON",
              r.is_json, f"content-type={r.content_type}")
        data = r.get_json()
        check("/api/stats/anxiety — список",
              isinstance(data, list))
        check(
            "Каждый элемент содержит 'date' и 'anxiety_level'",
            all("date" in d and "anxiety_level" in d for d in data),
            f"sample={data[:1]}",
        )

        r7 = c7.get("/ru/api/stats/anxiety?days=7")
        data7 = r7.get_json()
        check("/api/stats/anxiety?days=7 — JSON, статус 200",
              r7.status_code == 200 and isinstance(data7, list))
        check(
            "?days=7 не возвращает данные старше 7 дней",
            all(
                date.fromisoformat(d["date"]) >= today - timedelta(days=7)
                for d in data7
            ),
        )

        r = c7.get("/ru/api/stats/tasks")
        check("GET /api/stats/tasks — 200",
              r.status_code == 200, f"status={r.status_code}")
        check("/api/stats/tasks — JSON список",
              r.is_json and isinstance(r.get_json(), list))
        check(
            "Каждый элемент содержит 'week' и 'count'",
            all("week" in d and "count" in d for d in r.get_json()),
        )

        r = c7.get("/ru/api/stats/summary")
        check("GET /api/stats/summary — 200",
              r.status_code == 200, f"status={r.status_code}")
        check("/api/stats/summary — JSON", r.is_json)
        smry = r.get_json()
        for key in ("streak", "xp", "level", "total_tasks_completed", "avg_anxiety"):
            check(f"/api/stats/summary содержит '{key}'", key in smry,
                  f"keys={list(smry.keys())}")

        r = c7.get("/ru/api/stats/comparison")
        check("GET /api/stats/comparison — 200",
              r.status_code == 200, f"status={r.status_code}")
        cmp_api = r.get_json()
        for key in ("current_week_avg", "previous_week_avg", "change_pct", "trend"):
            check(f"/api/stats/comparison содержит '{key}'", key in cmp_api,
                  f"keys={list(cmp_api.keys())}")

        # ============================================================
        # 10. Изоляция данных
        # ============================================================
        print()
        print("--- 10. Изоляция данных между пользователями ---")
        userA = make_user(
            db, User, "isolA", "isolA@test.com", "pass1234",
            xp=999, streak=42,
        )
        userB = make_user(
            db, User, "isolB", "isolB@test.com", "pass1234",
            xp=1, streak=1,
        )
        # У A — 3 записи, у B — 1 запись
        for offset, lvl in enumerate([8, 9, 10]):
            db.session.add(DailyEntry(
                user_id=userA.id,
                date=today - timedelta(days=offset),
                anxiety_level=lvl,
                text=f"A entry {offset}",
            ))
        db.session.add(DailyEntry(
            user_id=userB.id, date=today, anxiety_level=2, text="B only",
        ))
        db.session.commit()

        clientA = login_client(app, "isolA@test.com", "pass1234")
        clientB = login_client(app, "isolB@test.com", "pass1234")

        histA = clientA.get("/ru/api/stats/anxiety").get_json()
        histB = clientB.get("/ru/api/stats/anxiety").get_json()
        check("A видит ровно 3 записи", len(histA) == 3, f"got={len(histA)}")
        check("B видит ровно 1 запись", len(histB) == 1, f"got={len(histB)}")
        check(
            "API не отдаёт записи чужого пользователя",
            all(h["anxiety_level"] in (8, 9, 10) for h in histA)
            and histB[0]["anxiety_level"] == 2,
        )

        smryA = clientA.get("/ru/api/stats/summary").get_json()
        smryB = clientB.get("/ru/api/stats/summary").get_json()
        check("summary A: streak == 42", smryA["streak"] == 42,
              f"got={smryA['streak']}")
        check("summary B: streak == 1", smryB["streak"] == 1,
              f"got={smryB['streak']}")
        check("summary A и B возвращают разные XP",
              smryA["xp"] != smryB["xp"])

        # Дашборд: A не видит запись B
        dashA = clientA.get("/ru/dashboard/").data.decode("utf-8")
        check("Дашборд A не содержит запись B ('B only')",
              "B only" not in dashA)
        dashB = clientB.get("/ru/dashboard/").data.decode("utf-8")
        check("Дашборд B не содержит запись A ('A entry')",
              "A entry" not in dashB)

        # ============================================================
        # 11. Пустые данные (edge cases)
        # ============================================================
        print()
        print("--- 11. Пустые данные (новый пользователь) ---")
        userE = make_user(db, User, "empty", "empty@test.com", "pass1234")

        s_empty = StatsService.get_dashboard_stats(userE.id)
        check("empty: streak == 0", s_empty["streak"] == 0,
              f"got={s_empty['streak']}")
        check("empty: avg_anxiety == 0", s_empty["avg_anxiety"] == 0,
              f"got={s_empty['avg_anxiety']}")
        check("empty: total_entries == 0", s_empty["total_entries"] == 0)
        check("empty: total_tasks_completed == 0",
              s_empty["total_tasks_completed"] == 0)

        cE = login_client(app, "empty@test.com", "pass1234")
        r = cE.get("/ru/dashboard/")
        check("GET /dashboard/ для пустого пользователя — 200 (не падает)",
              r.status_code == 200, f"status={r.status_code}")

        r = cE.get("/ru/api/stats/anxiety")
        check("/api/stats/anxiety для пустого пользователя — 200",
              r.status_code == 200)
        check("/api/stats/anxiety для пустого пользователя — пустой список []",
              r.get_json() == [], f"got={r.get_json()}")

        r = cE.get("/ru/api/stats/comparison")
        check("/api/stats/comparison для пустого пользователя — 200",
              r.status_code == 200)
        cmp_e = r.get_json()
        check(
            "comparison: trend == 'stable' на пустых данных",
            cmp_e.get("trend") == "stable",
            f"got={cmp_e}",
        )
        check(
            "comparison: change_pct адекватен (0 на пустых данных)",
            cmp_e.get("change_pct") in (0, 0.0),
            f"got={cmp_e.get('change_pct')}",
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
    exit(0 if success else 1)
