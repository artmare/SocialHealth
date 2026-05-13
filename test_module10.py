"""
test_module10.py — проверка инфраструктуры тестирования и CI/CD.
Запуск: python test_module10.py
"""

import sys
import os
import re
import subprocess
import time

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

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


def count_test_functions(content):
    if not content:
        return 0
    return len(re.findall(r"^\s*def\s+test_", content, re.MULTILINE))


def main():
    print("=" * 60)
    print("=== ТЕСТИРОВАНИЕ МОДУЛЯ 10: ТЕСТЫ И CI/CD ===")
    print("=" * 60)
    print()

    # ============================================================
    # 1. Структура файлов
    # ============================================================
    print("--- 1. Структура файлов ---")
    files = {
        "tests/conftest.py":              "conftest.py",
        "tests/test_auth.py":             "test_auth.py",
        "tests/test_diary.py":            "test_diary.py",
        "tests/test_tasks.py":            "test_tasks.py",
        "tests/test_ai_service.py":       "test_ai_service.py",
        "tests/test_dashboard.py":        "test_dashboard.py",
        "tests/test_sos.py":              "test_sos.py",
        "tests/test_profile.py":          "test_profile.py",
        "tests/test_tips.py":             "test_tips.py",
        "tests/test_models.py":           "test_models.py",
        ".github/workflows/ci.yml":       "CI workflow",
        "Procfile":                       "Procfile",
        ".env.example":                   ".env.example",
        "README.md":                      "README.md",
    }
    contents = {}
    for path, label in files.items():
        contents[path] = read_file(path)
        check(f"Файл {label} существует", contents[path] is not None,
              f"path={path}")

    conftest = contents.get("tests/conftest.py") or ""
    ci_yml   = contents.get(".github/workflows/ci.yml") or ""
    procfile = contents.get("Procfile") or ""
    env_ex   = contents.get(".env.example") or ""
    readme   = contents.get("README.md") or ""

    # ============================================================
    # 2. conftest.py содержит фикстуры
    # ============================================================
    print()
    print("--- 2. conftest.py: фикстуры ---")
    check("conftest содержит 'def app'", "def app" in conftest)
    check("conftest содержит 'def client'", "def client" in conftest)
    check(
        "conftest содержит 'def sample_user' / 'def test_user'",
        "def sample_user" in conftest or "def test_user" in conftest,
    )
    check(
        "conftest содержит 'def auth_headers' / 'def token' / 'def jwt'",
        "def auth_headers" in conftest
        or "def token" in conftest
        or "def jwt" in conftest,
    )
    check(
        "conftest содержит 'TestingConfig' или 'testing'",
        "TestingConfig" in conftest or "testing" in conftest,
    )
    check(
        "conftest содержит 'db.create_all' и ('db.drop_all' или 'rollback')",
        "db.create_all" in conftest
        or "_db.create_all" in conftest,
    )
    check(
        "conftest содержит teardown ('drop_all' или 'rollback')",
        "drop_all" in conftest or "rollback" in conftest,
    )

    # ============================================================
    # 3. Количество тестов в каждом файле
    # ============================================================
    print()
    print("--- 3. Количество тестов в файлах ---")
    requirements = {
        "tests/test_auth.py":       6,
        "tests/test_diary.py":      5,
        "tests/test_tasks.py":      8,
        "tests/test_ai_service.py": 5,
        "tests/test_dashboard.py":  4,
        "tests/test_sos.py":        3,
        "tests/test_profile.py":    5,
        "tests/test_tips.py":       3,
        "tests/test_models.py":     8,
    }
    total_tests = 0
    for path, minimum in requirements.items():
        c = count_test_functions(contents.get(path) or "")
        total_tests += c
        check(
            f"{os.path.basename(path)}: ≥ {minimum} test-функций",
            c >= minimum,
            f"got={c}",
        )
    check(
        f"Всего тест-функций ≥ 47 (получено {total_tests})",
        total_tests >= 47,
        f"got={total_tests}",
    )

    # ============================================================
    # 4. AI тесты используют mock
    # ============================================================
    print()
    print("--- 4. AI тесты используют mock ---")
    ai_content = contents.get("tests/test_ai_service.py") or ""
    check(
        "test_ai_service.py содержит 'mock'/'patch'/'MagicMock'",
        "mock" in ai_content.lower()
        or "patch" in ai_content
        or "MagicMock" in ai_content,
    )
    # Нет ли захардкоженного ключа — ищем sk-ant-... / похожие паттерны
    has_real_key = bool(
        re.search(r"sk-ant-[A-Za-z0-9\-_]{10,}", ai_content)
        or re.search(r"ANTHROPIC_API_KEY\s*=\s*[\"'][A-Za-z0-9\-_]{20,}[\"']",
                     ai_content)
    )
    check(
        "test_ai_service.py НЕ содержит реальный API ключ",
        not has_real_key,
    )

    diary_content = contents.get("tests/test_diary.py") or ""
    check(
        "test_diary.py содержит mock для AI (patch/mock)",
        "patch" in diary_content or "mock" in diary_content.lower(),
    )

    # ============================================================
    # 5. CI/CD (.github/workflows/ci.yml)
    # ============================================================
    print()
    print("--- 5. CI/CD файл ---")
    check("ci.yml содержит 'pytest'", "pytest" in ci_yml)
    check("ci.yml содержит python-version 3.11",
          re.search(r"python-version\s*:\s*['\"]?3\.11", ci_yml) is not None)
    check("ci.yml содержит 'pip install -r requirements.txt'",
          "pip install -r requirements.txt" in ci_yml)
    check(
        "ci.yml содержит trigger на push и/или pull_request",
        "push:" in ci_yml or "pull_request:" in ci_yml,
    )
    check(
        "ci.yml содержит 'FLASK_CONFIG: testing' или аналог",
        "FLASK_CONFIG" in ci_yml or "FLASK_ENV" in ci_yml,
    )
    # опционально — deploy/Railway. Просто отметим.
    if "railway" in ci_yml.lower() or "deploy" in ci_yml.lower():
        check("ci.yml содержит deploy-шаг (Railway или иной)", True)

    # ============================================================
    # 6. Procfile
    # ============================================================
    print()
    print("--- 6. Procfile ---")
    check("Procfile содержит 'gunicorn'", "gunicorn" in procfile)
    check("Procfile содержит 'create_app'", "create_app" in procfile)
    check(
        "Procfile содержит '--workers' или '-w'",
        "--workers" in procfile or re.search(r"\s-w\s", procfile) is not None,
    )

    # ============================================================
    # 7. .env.example
    # ============================================================
    print()
    print("--- 7. .env.example ---")
    for key in ("SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL",
                "ANTHROPIC_API_KEY", "FLASK_CONFIG"):
        check(f".env.example содержит '{key}'", key in env_ex)

    # Реальных секретов быть не должно — все значения placeholder.
    suspicious = re.search(r"sk-ant-[A-Za-z0-9\-_]{15,}", env_ex)
    check(
        ".env.example НЕ содержит реальный ANTHROPIC ключ",
        suspicious is None,
        f"matched={suspicious.group(0) if suspicious else None}",
    )

    # ============================================================
    # 8. README.md
    # ============================================================
    print()
    print("--- 8. README.md ---")
    check("README содержит название 'SocialHealth'", "SocialHealth" in readme)
    check(
        "README содержит инструкцию установки",
        "pip install" in readme or "requirements.txt" in readme,
    )
    check("README содержит 'pytest'", "pytest" in readme)
    check(
        "README содержит 'flask run' или команду запуска",
        "flask run" in readme or "python run.py" in readme
        or "gunicorn" in readme,
    )
    check(
        "README содержит дисклеймер (немедицинский сервис)",
        "не является медицинским" in readme
        or "не медицинск" in readme.lower()
        or "немедицинск" in readme.lower(),
    )
    check(
        "README содержит телефон доверия 8-800-2000-122",
        "8-800-2000-122" in readme or "88002000122" in readme,
    )

    # ============================================================
    # 9. Запуск pytest
    # ============================================================
    print()
    print("--- 9. Запуск pytest ---")

    # 9a. collect-only
    try:
        cp = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
            capture_output=True, text=True, timeout=120,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        collected = 0
        m = re.search(r"(\d+)\s+tests?\s+collected", cp.stdout)
        if m:
            collected = int(m.group(1))
        else:
            collected = cp.stdout.count("::test_")
        check(
            f"pytest --collect-only: собрано ≥ 47 тестов (got={collected})",
            collected >= 47,
            f"stdout tail: {cp.stdout[-300:]}",
        )
    except Exception as e:
        check("pytest --collect-only выполняется без ошибок", False, str(e))
        collected = 0

    # 9b. полный прогон
    pytest_passed = pytest_failed = pytest_total = 0
    duration = 0.0
    pytest_output = ""
    try:
        t0 = time.time()
        cp = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short",
             "-W", "ignore"],
            capture_output=True, text=True, timeout=180,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        duration = time.time() - t0
        pytest_output = cp.stdout + cp.stderr

        m = re.search(
            r"(?:(\d+)\s+passed)?(?:,\s+(\d+)\s+failed)?(?:,\s+(\d+)\s+(?:warnings?|skipped|errors?))?",
            pytest_output,
        )
        m_pass = re.search(r"(\d+)\s+passed", pytest_output)
        m_fail = re.search(r"(\d+)\s+failed", pytest_output)
        pytest_passed = int(m_pass.group(1)) if m_pass else 0
        pytest_failed = int(m_fail.group(1)) if m_fail else 0
        pytest_total = pytest_passed + pytest_failed

        check(
            f"pytest: все тесты ПРОШЛИ ({pytest_passed} passed, {pytest_failed} failed)",
            cp.returncode == 0 and pytest_failed == 0,
            f"returncode={cp.returncode}",
        )
        check(
            f"pytest выполнен за < 30 секунд (фактически {duration:.1f}s)",
            duration < 30.0,
            f"duration={duration:.1f}s",
        )
    except subprocess.TimeoutExpired:
        check("pytest полный прогон укладывается в 180с", False, "timeout")
    except Exception as e:
        check("pytest полный прогон выполняется без ошибок", False, str(e))

    # ============================================================
    # 10. Покрытие ключевых сценариев
    # ============================================================
    print()
    print("--- 10. Покрытие ключевых сценариев ---")
    all_tests_text = "\n".join(
        (contents.get(p) or "") for p in requirements
    )

    scenarios = [
        ("регистрация (/auth/register)",
         r"/auth/register|test_register"),
        ("логин (/auth/login)",
         r"/auth/login|test_login"),
        ("создание записи дневника",
         r"/diary/new|test_create_entry"),
        ("выполнение задания + XP",
         r"complete_task|test_complete.*xp|xp_earned"),
        ("level up",
         r"levelup|leveled_up|test_.*level"),
        ("streak",
         r"streak"),
        ("AI с mock",
         r"patch.*ai|mock.*ai|MagicMock.*ai|AIService"),
        ("SOS без авторизации",
         r"sos.*no_auth|sos.*without|/sos/.*\b200\b|test_sos"),
        ("изоляция данных (A ≠ B)",
         r"isolation|second_user|other_user|other_private|forbidden"),
    ]
    for name, pattern in scenarios:
        ok = re.search(pattern, all_tests_text, re.IGNORECASE) is not None
        check(f"Есть тест на: {name}", ok)

    # ============================================================
    # Итог
    # ============================================================
    print()
    print("=" * 60)
    print("=== ЗАПУСК PYTEST (хвост вывода) ===")
    print("=" * 60)
    if pytest_output:
        tail = "\n".join(pytest_output.splitlines()[-20:])
        print(tail)

    passed = sum(1 for ok, _, _ in results if ok)
    failed = sum(1 for ok, _, _ in results if not ok)
    total = passed + failed

    print()
    for ok, desc, err in results:
        if ok:
            print(f"[OK] {desc}")
        else:
            print(f"[FAIL] {desc} — ошибка: {err}")

    print()
    print("=" * 60)
    print(f"=== ИТОГ: Пройдено {passed} из {total} проверок ===")
    if pytest_total:
        print(f"=== PYTEST: {pytest_passed} passed, "
              f"{pytest_failed} failed из {pytest_total} total "
              f"(время {duration:.1f}s) ===")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
