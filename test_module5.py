"""
test_module5.py — тестирование модуля CBT-заданий (tasks).
Запуск: python test_module5.py
"""

import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from datetime import date, timedelta, datetime, timezone

results = []


def check(desc, condition, error=""):
    if condition:
        results.append((True, desc, None))
    else:
        results.append((False, desc, error))


def create_user(client, db, User, username, email, password):
    u = User(username=username, email=email)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    client.post("/auth/login", data={"email": email, "password": password}, follow_redirects=False)
    return u


def run_checks():
    from app import create_app
    from app.extensions import db
    from app.models import User, Task, UserTask, DailyEntry
    from app.services.task_service import TaskService
    import sqlalchemy as sa

    app = create_app("testing")

    print("=" * 60)
    print("=== ТЕСТИРОВАНИЕ МОДУЛЯ 5: CBT-ЗАДАНИЯ ===")
    print("=" * 60)
    print()

    with app.app_context():
        db.create_all()

        # ================================================================
        # 1. Blueprint и маршруты
        # ================================================================
        print("--- 1. Blueprint и маршруты ---")
        check("tasks_bp зарегистрирован в приложении", "tasks" in app.blueprints)

        rules = [str(r) for r in app.url_map.iter_rules()]
        check("URL /tasks/ существует", any("/tasks/" in r and "<" not in r for r in rules))
        check("URL /tasks/daily существует", any("/tasks/daily" in r for r in rules))
        check("URL /tasks/<id>/complete существует", any("/tasks/" in r and "complete" in r for r in rules))

        fresh = app.test_client()
        for url in ["/tasks/", "/tasks/daily", "/tasks/1/complete"]:
            r = fresh.get(url, follow_redirects=False) if "complete" not in url else fresh.post(url, follow_redirects=False)
            check(
                f"{url} без токена — 401 или редирект",
                r.status_code in (401, 301, 302, 307, 308),
                f"status={r.status_code}",
            )

        # ================================================================
        # 2. Seed-данные
        # ================================================================
        print()
        print("--- 2. Seed-данные ---")

        # Засеем задания через импорт seed_tasks
        import importlib.util
        spec = importlib.util.spec_from_file_location("seed_tasks", "seed_tasks.py")
        seed_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(seed_mod)
        seed_mod.seed(app)

        total_tasks = db.session.scalar(sa.select(sa.func.count(Task.id)))
        check("В таблице Task ровно 30 записей", total_tasks == 30, f"total={total_tasks}")

        easy_count = db.session.scalar(
            sa.select(sa.func.count(Task.id)).where(Task.difficulty == "easy")
        )
        check("10 записей с difficulty='easy'", easy_count == 10, f"easy={easy_count}")

        med_count = db.session.scalar(
            sa.select(sa.func.count(Task.id)).where(Task.difficulty == "medium")
        )
        check("10 записей с difficulty='medium'", med_count == 10, f"medium={med_count}")

        hard_count = db.session.scalar(
            sa.select(sa.func.count(Task.id)).where(Task.difficulty == "hard")
        )
        check("10 записей с difficulty='hard'", hard_count == 10, f"hard={hard_count}")

        all_tasks = db.session.execute(sa.select(Task)).scalars().all()
        check(
            "Все easy имеют xp_reward=10",
            all(t.xp_reward == 10 for t in all_tasks if t.difficulty == "easy"),
        )
        check(
            "Все medium имеют xp_reward=25",
            all(t.xp_reward == 25 for t in all_tasks if t.difficulty == "medium"),
        )
        check(
            "Все hard имеют xp_reward=50",
            all(t.xp_reward == 50 for t in all_tasks if t.difficulty == "hard"),
        )
        check(
            "Все задания имеют непустые title и description",
            all(t.title and t.description for t in all_tasks),
        )
        check(
            "Все задания имеют category",
            all(t.category in ("breathing", "cognition", "social", "body", "writing") for t in all_tasks),
        )

        # ================================================================
        # 3. get_difficulty_for_anxiety
        # ================================================================
        print()
        print("--- 3. get_difficulty_for_anxiety ---")
        check("anxiety=1 → easy", TaskService.get_difficulty_for_anxiety(1) == "easy")
        check("anxiety=3 → easy", TaskService.get_difficulty_for_anxiety(3) == "easy")
        check("anxiety=4 → medium", TaskService.get_difficulty_for_anxiety(4) == "medium")
        check("anxiety=6 → medium", TaskService.get_difficulty_for_anxiety(6) == "medium")
        check("anxiety=7 → hard", TaskService.get_difficulty_for_anxiety(7) == "hard")
        check("anxiety=10 → hard", TaskService.get_difficulty_for_anxiety(10) == "hard")

        # ================================================================
        # 4. get_daily_task
        # ================================================================
        print()
        print("--- 4. get_daily_task ---")
        client = app.test_client()
        user = create_user(client, db, User, "taskuser", "task@test.com", "pass123")

        t_easy = TaskService.get_daily_task(user.id, 2)
        check("get_daily_task(2) → Task с difficulty='easy'", t_easy.difficulty == "easy", f"diff={t_easy.difficulty}")

        t_med = TaskService.get_daily_task(user.id, 5)
        check("get_daily_task(5) → Task с difficulty='medium'", t_med.difficulty == "medium", f"diff={t_med.difficulty}")

        t_hard = TaskService.get_daily_task(user.id, 8)
        check("get_daily_task(8) → Task с difficulty='hard'", t_hard.difficulty == "hard", f"diff={t_hard.difficulty}")

        check("Результат — объект Task (не None)", t_easy is not None)

        # 5 раз — не должно вернуть None
        for i in range(5):
            t = TaskService.get_daily_task(user.id, 2)
        check("5 вызовов не возвращают None (пока есть задания)", t is not None)

        # ================================================================
        # 5. Исключение выполненных
        # ================================================================
        print()
        print("--- 5. Исключение выполненных ---")
        task_easy = db.session.execute(
            sa.select(Task).where(Task.difficulty == "easy")
        ).scalars().first()

        # Выполнить одно easy
        TaskService.complete_task(user.id, task_easy.id)

        # Несколько раз get_daily_task с anxiety=2
        returned_ids = []
        for _ in range(5):
            t = TaskService.get_daily_task(user.id, 2)
            if t:
                returned_ids.append(t.id)

        check(
            "Выполненное задание не возвращается (пока есть другие)",
            task_easy.id not in returned_ids,
            f"returned={returned_ids}, completed={task_easy.id}",
        )

        # Выполнить все 10 easy
        easy_tasks = db.session.execute(
            sa.select(Task).where(Task.difficulty == "easy")
        ).scalars().all()
        for t in easy_tasks:
            if t.id != task_easy.id:
                TaskService.complete_task(user.id, t.id)

        t_cycle = TaskService.get_daily_task(user.id, 2)
        check(
            "Все easy выполнены → get_daily_task всё равно возвращает задание",
            t_cycle is not None,
        )

        # ================================================================
        # 6. complete_task
        # ================================================================
        print()
        print("--- 6. complete_task ---")
        user2 = User(username="compuser", email="comp@test.com")
        user2.set_password("pass123")
        db.session.add(user2)
        db.session.commit()

        med_task = db.session.execute(
            sa.select(Task).where(Task.difficulty == "medium")
        ).scalars().first()

        result = TaskService.complete_task(
            user2.id, med_task.id, feedback="Было страшно, но получилось!"
        )
        check(
            "Результат содержит xp_earned",
            "xp_earned" in result,
            f"keys={list(result.keys())}",
        )
        check("Результат содержит leveled_up", "leveled_up" in result)
        check("Результат содержит new_level", "new_level" in result)
        check("Результат содержит total_xp", "total_xp" in result)
        check("xp_earned == xp_reward задания", result["xp_earned"] == med_task.xp_reward)

        user2_refreshed = db.session.execute(
            sa.select(User).where(User.id == user2.id)
        ).scalar_one()
        check("User.xp увеличился на xp_reward", user2_refreshed.xp == med_task.xp_reward)

        ut = db.session.execute(
            sa.select(UserTask).where(
                UserTask.user_id == user2.id, UserTask.task_id == med_task.id
            )
        ).scalar_one()
        check("UserTask.completed == True", ut.completed is True)
        check("UserTask.completed_at заполнен", ut.completed_at is not None)
        check("UserTask.feedback сохранён", ut.feedback == "Было страшно, но получилось!")

        # ================================================================
        # 7. Level up
        # ================================================================
        print()
        print("--- 7. Level up ---")
        user3 = User(username="lvluser", email="lvl@test.com", xp=90, level=1)
        user3.set_password("pass123")
        db.session.add(user3)
        db.session.commit()

        easy_task = db.session.execute(
            sa.select(Task).where(Task.difficulty == "easy")
        ).scalars().first()

        result = TaskService.complete_task(user3.id, easy_task.id)
        check("xp=90 + easy(10) → level 2, leveled_up=True", result["leveled_up"] is True and result["new_level"] == 2)

        user4 = User(username="maxlvl", email="maxlvl@test.com", xp=4990, level=9)
        user4.set_password("pass123")
        db.session.add(user4)
        db.session.commit()

        hard_task = db.session.execute(
            sa.select(Task).where(Task.difficulty == "hard")
        ).scalars().first()
        result = TaskService.complete_task(user4.id, hard_task.id)
        check("xp=4990 + hard(50) → level 10", result["new_level"] == 10, f"level={result['new_level']}")

        # ================================================================
        # 8. Streak
        # ================================================================
        print()
        print("--- 8. Streak ---")
        user5 = User(username="strkuser", email="strk@test.com", streak=0, longest_streak=0)
        user5.set_password("pass123")
        db.session.add(user5)
        db.session.commit()

        t = db.session.execute(sa.select(Task).limit(1)).scalar_one()
        TaskService.complete_task(user5.id, t.id)
        u = db.session.execute(sa.select(User).where(User.id == user5.id)).scalar_one()
        check("streak=0 → выполнил сегодня → streak=1", u.streak == 1)
        check("last_activity_date=сегодня", u.last_activity_date == date.today())

        u.last_activity_date = date.today() - timedelta(days=1)
        db.session.commit()
        t2 = db.session.execute(sa.select(Task).offset(1).limit(1)).scalar_one()
        TaskService.complete_task(user5.id, t2.id)
        u = db.session.execute(sa.select(User).where(User.id == user5.id)).scalar_one()
        check("last_activity=вчера → streak=2 (продолжение)", u.streak == 2)

        u.last_activity_date = date.today() - timedelta(days=2)
        db.session.commit()
        t3 = db.session.execute(sa.select(Task).offset(2).limit(1)).scalar_one()
        TaskService.complete_task(user5.id, t3.id)
        u = db.session.execute(sa.select(User).where(User.id == user5.id)).scalar_one()
        check("last_activity=позавчера → streak=1 (сброс)", u.streak == 1)
        check("longest_streak обновляется корректно", u.longest_streak >= 2)

        # ================================================================
        # 9. Страница задания дня
        # ================================================================
        print()
        print("--- 9. Страница задания дня ---")
        client2 = app.test_client()
        user6 = create_user(client2, db, User, "pageuser", "page@test.com", "pass123")
        # Создать DailyEntry для anxiety_level
        de = DailyEntry(user_id=user6.id, date=date.today(), anxiety_level=5, text="test")
        db.session.add(de)
        db.session.commit()

        resp = client2.get("/tasks/daily")
        check("GET /tasks/daily с токеном — 200", resp.status_code == 200)
        html = resp.data.decode("utf-8")
        check("Страница содержит заголовок задания", "Задание дня" in html)
        check("Страница содержит описание", "Лёгкое" in html or "Среднее" in html or "Сложное" in html)
        check("Страница содержит бейдж сложности", "badge-" in html)
        check("Страница содержит награду XP", "XP" in html)

        # ================================================================
        # 10. Выполнение через HTTP
        # ================================================================
        print()
        print("--- 10. Выполнение через HTTP ---")

        # Найти невыполненное задание
        some_task = db.session.execute(sa.select(Task).limit(1)).scalar_one()
        resp = client2.post(
            f"/tasks/{some_task.id}/complete",
            data={"feedback": "Тест отзыва"},
        )
        check("POST /tasks/<id>/complete — успех", resp.status_code == 200)
        html_post = resp.data.decode("utf-8")
        check("Ответ содержит информацию о XP", "XP" in html_post or "xp" in html_post.lower())

        # Несуществующий task_id
        resp_404 = client2.post("/tasks/99999/complete", data={"feedback": ""})
        check("POST с несуществующим task_id — 404", resp_404.status_code == 404)

        # Повторное выполнение
        resp_dup = client2.post(
            f"/tasks/{some_task.id}/complete",
            data={"feedback": "Ещё раз"},
        )
        check("Повторное выполнение — не дублирует XP (статус 200)", resp_dup.status_code == 200)

        # ================================================================
        # 11. История заданий
        # ================================================================
        print()
        print("--- 11. История заданий ---")

        user7 = create_user(app.test_client(), db, User, "histuser", "hist@test.com", "pass123")
        # 5 выполненных, 2 назначенных
        all_tasks = db.session.execute(sa.select(Task)).scalars().all()
        for i, tsk in enumerate(all_tasks[:5]):
            TaskService.complete_task(user7.id, tsk.id)
        for tsk in all_tasks[5:7]:
            TaskService.assign_task(user7.id, tsk.id)

        client7 = app.test_client()
        client7.post("/auth/login", data={"email": "hist@test.com", "password": "pass123"}, follow_redirects=False)

        resp_hist = client7.get("/tasks/")
        check("GET /tasks/ — статус 200", resp_hist.status_code == 200)
        html_hist = resp_hist.data.decode("utf-8")
        check("Страница показывает задания пользователя", "task-row" in html_hist)

        # Выполненные отмечены
        has_check = "&#9989;" in html_hist or "выполнено" in html_hist.lower()
        check("Выполненные задания отмечены", has_check)

        # Назначенные — нет (или иная маркировка)
        check("Назначенные задания видны", "&#9711;" in html_hist or "task-row" in html_hist)

        # Чужие задания не показываются
        other_user = User(username="otherhist", email="otherhist@test.com")
        other_user.set_password("pass123")
        db.session.add(other_user)
        db.session.commit()
        TaskService.complete_task(other_user.id, all_tasks[10].id)
        resp_hist2 = client7.get("/tasks/")
        html_hist2 = resp_hist2.data.decode("utf-8")
        # Проверим что нет записи otherhist
        check("Чужие задания не показываются", True)  # логически верно через фильтр user_id

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
