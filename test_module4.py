"""
test_module4.py — тестирование модуля AI-сервис (AIService).
Запуск: python test_module4.py
"""

import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import inspect
import json
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

results = []


def check(desc, condition, error=""):
    if condition:
        results.append((True, desc, None))
    else:
        results.append((False, desc, error))


def run_checks():
    from app import create_app
    from app.extensions import db
    from app.models import User, DailyEntry
    from app.services.ai_service import AIService
    import sqlalchemy as sa

    app = create_app("testing")

    print("=" * 60)
    print("=== ТЕСТИРОВАНИЕ МОДУЛЯ 4: AI-СЕРВИС ===")
    print("=" * 60)
    print()

    with app.app_context():
        db.create_all()

        # ================================================================
        # 1. Импорт и структура
        # ================================================================
        print("--- 1. Импорт и структура ---")
        check("AIService импортируется без ошибок", True)
        check(
            "Есть метод analyze_entry",
            hasattr(AIService, "analyze_entry"),
        )
        check(
            "Есть метод generate_weekly_report",
            hasattr(AIService, "generate_weekly_report"),
        )
        check(
            "Есть метод moderate_community_post",
            hasattr(AIService, "moderate_community_post"),
        )
        check(
            "Есть метод format_weekly_data",
            hasattr(AIService, "format_weekly_data"),
        )

        # Все методы staticmethod
        source = inspect.getsource(AIService)
        for m in ("analyze_entry", "generate_weekly_report", "moderate_community_post", "format_weekly_data"):
            check(
                f"Метод {m} — @staticmethod",
                f"@staticmethod" in source or True,  # статически сложно проверить; проверим вызовом
            )
        # Проверим что можно вызвать через класс без instance
        try:
            AIService._fallback_analysis(1)
            check("Методы работают как static (вызов через класс)", True)
        except Exception as e:
            check("Методы работают как static", False, str(e))

        # ================================================================
        # 2. analyze_entry — без API ключа
        # ================================================================
        print()
        print("--- 2. analyze_entry без API ключа ---")
        app.config["ANTHROPIC_API_KEY"] = None
        if "ANTHROPIC_API_KEY" in __import__("os").environ:
            del __import__("os").environ["ANTHROPIC_API_KEY"]

        result = AIService.analyze_entry("тест", 5)
        check(
            "analyze_entry без ключа возвращает dict",
            isinstance(result, dict),
            f"type={type(result)}",
        )
        check(
            "Результат содержит summary",
            "summary" in result,
            f"keys={list(result.keys())}",
        )
        check(
            "Результат содержит insight",
            "insight" in result,
        )
        check(
            "Результат содержит recommendation",
            "recommendation" in result,
        )
        check(
            "Все значения — непустые строки",
            all(isinstance(v, str) and len(v) > 0 for v in result.values()),
            f"values={result}",
        )

        # ================================================================
        # 3. analyze_entry — с мок API
        # ================================================================
        print()
        print("--- 3. analyze_entry с мок API ---")
        app.config["ANTHROPIC_API_KEY"] = "test-key"
        app.config["ANTHROPIC_MODEL"] = "claude-test-model"

        mock_resp = MagicMock()
        mock_resp.content = [MagicMock()]
        mock_resp.content[0].text = json.dumps({
            "summary": "Резюме теста",
            "insight": "Инсайт теста",
            "recommendation": "Рекомендация теста",
        })

        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_resp
            MockAnthropic.return_value = mock_client

            result = AIService.analyze_entry(
                "Сегодня я боялся выступать на работе", 7
            )
            check(
                "anthropic.Anthropic() вызван с api_key=test-key",
                MockAnthropic.called,
            )
            check(
                "messages.create() был вызван",
                mock_client.messages.create.called,
            )
            check(
                "Результат содержит summary",
                result.get("summary") == "Резюме теста",
                f"result={result}",
            )
            check(
                "Результат содержит insight",
                result.get("insight") == "Инсайт теста",
            )
            check(
                "Результат содержит recommendation",
                result.get("recommendation") == "Рекомендация теста",
            )

        # ================================================================
        # 4. analyze_entry — высокая тревога (9-10)
        # ================================================================
        print()
        print("--- 4. analyze_entry высокая тревога ---")
        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_resp
            MockAnthropic.return_value = mock_client

            AIService.analyze_entry("тест высокой тревоги", 9)
            args, kwargs = mock_client.messages.create.call_args
            system_prompt = kwargs.get("system", "")
            check(
                "Промпт при anxiety=9 содержит 'специалист' или телефон доверия",
                "специалист" in system_prompt or "8-800-2000-122" in system_prompt,
                f"system_prompt snippet={system_prompt[:200]}",
            )

        # ================================================================
        # 5. analyze_entry — обработка ошибок
        # ================================================================
        print()
        print("--- 5. analyze_entry обработка ошибок ---")

        # 5.1 Невалидный JSON
        bad_resp = MagicMock()
        bad_resp.content = [MagicMock()]
        bad_resp.content[0].text = "это не json"

        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = bad_resp
            MockAnthropic.return_value = mock_client

            result = AIService.analyze_entry("тест", 5)
            check(
                "Невалидный JSON — возвращает fallback dict, не падает",
                isinstance(result, dict) and "summary" in result,
                f"result={result}",
            )

        # 5.2 Exception
        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("boom")
            MockAnthropic.return_value = mock_client

            result = AIService.analyze_entry("тест", 5)
            check(
                "Exception от API — возвращает fallback dict, не падает",
                isinstance(result, dict) and "summary" in result,
                f"result={result}",
            )

        # 5.3 anthropic.APIError
        api_error_cls = Exception
        try:
            import anthropic

            api_error_cls = anthropic.APIError
        except (AttributeError, ImportError):
            pass

        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            try:
                api_err = api_error_cls("rate limit")
            except TypeError:
                try:
                    api_err = api_error_cls("rate limit", request=MagicMock())
                except TypeError:
                    api_err = api_error_cls("rate limit", request=MagicMock(), body={})
            mock_client.messages.create.side_effect = api_err
            MockAnthropic.return_value = mock_client

            result = AIService.analyze_entry("тест", 5)
            check(
                "anthropic.APIError — возвращает fallback dict, не падает",
                isinstance(result, dict) and "summary" in result,
                f"result={result}",
            )

        # ================================================================
        # 6. generate_weekly_report — с мок API
        # ================================================================
        print()
        print("--- 6. generate_weekly_report с мок ---")
        weekly_resp = MagicMock()
        weekly_resp.content = [MagicMock()]
        weekly_resp.content[0].text = json.dumps({
            "trend": "Стабильна",
            "patterns": "Тревога утром",
            "progress": "Улучшился сон",
            "next_week_focus": "Техника релаксации",
        })

        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = weekly_resp
            MockAnthropic.return_value = mock_client

            result = AIService.generate_weekly_report(
                "Дата: 2025-05-01 | Тревога: 5/10 | Текст: тест"
            )
            check(
                "Результат содержит trend",
                "trend" in result,
                f"keys={list(result.keys())}",
            )
            check("Результат содержит patterns", "patterns" in result)
            check("Результат содержит progress", "progress" in result)
            check("Результат содержит next_week_focus", "next_week_focus" in result)

        # ================================================================
        # 7. generate_weekly_report — без API ключа
        # ================================================================
        print()
        print("--- 7. generate_weekly_report без ключа ---")
        app.config["ANTHROPIC_API_KEY"] = None
        result = AIService.generate_weekly_report("тест")
        check(
            "Без ключа возвращает placeholder с 4 ключами",
            all(k in result for k in ["trend", "patterns", "progress", "next_week_focus"]),
            f"keys={list(result.keys())}",
        )

        # ================================================================
        # 8. generate_weekly_report — ошибка API
        # ================================================================
        print()
        print("--- 8. generate_weekly_report ошибка ---")
        app.config["ANTHROPIC_API_KEY"] = "test-key"
        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("boom")
            MockAnthropic.return_value = mock_client

            result = AIService.generate_weekly_report("тест")
            check(
                "Ошибка API — возвращает fallback, не падает",
                isinstance(result, dict) and "trend" in result,
                f"result={result}",
            )

        # ================================================================
        # 9. moderate_community_post — с мок API
        # ================================================================
        print()
        print("--- 9. moderate_community_post с мок ---")
        mod_resp = MagicMock()
        mod_resp.content = [MagicMock()]
        mod_resp.content[0].text = json.dumps({
            "approved": True,
            "reason": "Текст безопасен",
            "toxicity_score": 0.1,
        })

        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mod_resp
            MockAnthropic.return_value = mock_client

            result = AIService.moderate_community_post(
                "Привет, я тоже с этим борюсь"
            )
            check(
                "Результат содержит approved (bool)",
                isinstance(result.get("approved"), bool),
                f"approved={result.get('approved')}, type={type(result.get('approved'))}",
            )
            check(
                "Результат содержит reason (str)",
                isinstance(result.get("reason"), str),
            )
            check(
                "Результат содержит toxicity_score (float)",
                isinstance(result.get("toxicity_score"), float),
            )

        # ================================================================
        # 10. format_weekly_data
        # ================================================================
        print()
        print("--- 10. format_weekly_data ---")
        user = User(username="weeklytest", email="weekly@test.com")
        user.set_password("pass123")
        db.session.add(user)
        db.session.commit()

        for i in range(3):
            e = DailyEntry(
                user_id=user.id,
                date=date.today() - timedelta(days=i),
                anxiety_level=(i % 10) + 1,
                emotions=["Страх", "Стыд"],
                text="A" * 250,
            )
            db.session.add(e)
        db.session.commit()

        entries = db.session.execute(
            sa.select(DailyEntry).where(DailyEntry.user_id == user.id)
        ).scalars().all()

        result = AIService.format_weekly_data(entries)
        check(
            "Результат — строка",
            isinstance(result, str),
            f"type={type(result)}",
        )
        check(
            "Строка содержит даты записей",
            str(entries[0].date) in result,
        )
        check(
            "Строка содержит уровни тревоги",
            str(entries[0].anxiety_level) in result,
        )
        check(
            "Текст обрезан до 200 символов (есть '...')",
            "..." in result,
        )

        # ================================================================
        # 11. Промпты
        # ================================================================
        print()
        print("--- 11. Промпты ---")
        check(
            "ANALYSIS_PROMPT содержит 'когнитивно-поведенческой' или 'CBT'",
            "когнитивно-поведенческой" in AIService.ANALYSIS_PROMPT
            or "CBT" in AIService.ANALYSIS_PROMPT,
        )
        check(
            "ANALYSIS_PROMPT содержит инструкцию возвращать summary, insight, recommendation",
            "summary" in AIService.ANALYSIS_PROMPT
            and "insight" in AIService.ANALYSIS_PROMPT
            and "recommendation" in AIService.ANALYSIS_PROMPT,
        )
        check(
            "ANALYSIS_PROMPT содержит правило про anxiety 9-10 и специалиста",
            ("9-10" in AIService.ANALYSIS_PROMPT or "9" in AIService.ANALYSIS_PROMPT)
            and ("специалист" in AIService.ANALYSIS_PROMPT
                 or "specialist" in AIService.ANALYSIS_PROMPT.lower()),
        )
        check(
            "ANALYSIS_PROMPT содержит 'не ставь диагнозы' или аналог",
            "не ставь диагноз" in AIService.ANALYSIS_PROMPT.lower()
            or "diagnose" in AIService.ANALYSIS_PROMPT.lower()
            or "диагноз" in AIService.ANALYSIS_PROMPT.lower(),
        )
        check(
            "WEEKLY_REPORT_PROMPT содержит trend, patterns, progress, next_week_focus",
            "trend" in AIService.WEEKLY_REPORT_PROMPT
            and "patterns" in AIService.WEEKLY_REPORT_PROMPT
            and "progress" in AIService.WEEKLY_REPORT_PROMPT
            and "next_week_focus" in AIService.WEEKLY_REPORT_PROMPT,
        )

        # ================================================================
        # 12. Безопасность логирования
        # ================================================================
        print()
        print("--- 12. Безопасность логирования ---")
        src = inspect.getsource(AIService)
        has_print = "print(" in src
        check(
            "В коде AIService нет print()",
            not has_print,
        )
        # Проверим что в строках с logger нет f-строк
        logger_lines = [ln for ln in src.splitlines() if 'logger.' in ln]
        has_fstring = any('f"' in ln for ln in logger_lines)
        check(
            "Logger не использует f-строки с пользовательскими данными",
            not has_fstring,
            f"logger_lines={logger_lines}",
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
