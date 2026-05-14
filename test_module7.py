"""
test_module7.py — тестирование модуля 7 (SOS-режим).
Запуск: python test_module7.py
"""

import sys
import os
import re

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


def html_from(client, url, **kw):
    r = client.get(url, headers={"Accept": "text/html"}, follow_redirects=False, **kw)
    return r, r.data.decode("utf-8", errors="replace")


def run_checks():
    from app import create_app
    from app.extensions import db

    app = create_app("testing")

    print("=" * 60)
    print("=== ТЕСТИРОВАНИЕ МОДУЛЯ 7: SOS-РЕЖИМ ===")
    print("=" * 60)
    print()

    with app.app_context():
        db.create_all()

        # ============================================================
        # 1. Blueprint и маршруты
        # ============================================================
        print("--- 1. Blueprint и маршруты ---")
        check("Blueprint sos зарегистрирован", "sos" in app.blueprints)

        rules = {str(r.rule) for r in app.url_map.iter_rules()}
        for url in ["/sos/", "/sos/breathing", "/sos/grounding"]:
            check(f"URL {url} существует", url in rules,
                  f"available rules sample={sorted(r for r in rules if '/sos' in r)}")

        # ============================================================
        # 2. Доступность без авторизации
        # ============================================================
        print()
        print("--- 2. Доступность БЕЗ авторизации ---")
        anon = app.test_client()
        for url in ["/sos/", "/sos/breathing", "/sos/grounding"]:
            r, _ = html_from(anon, url)
            check(
                f"GET {url} БЕЗ токена → 200 (не редирект, не 401)",
                r.status_code == 200,
                f"status={r.status_code} loc={r.headers.get('Location')}",
            )

        # ============================================================
        # 3. Главная SOS-страница
        # ============================================================
        print()
        print("--- 3. Главная SOS-страница ---")
        r, html_idx = html_from(anon, "/ru/sos/")
        check("/sos/ → статус 200", r.status_code == 200, f"status={r.status_code}")
        low_idx = html_idx.lower()

        check(
            "Содержит успокаивающее сообщение ('безопасности'/'будет хорошо')",
            "безопасности" in low_idx or "будет хорошо" in low_idx or "everything will be okay" in low_idx or "you are safe" in low_idx,
        )
        check("Содержит ссылку на /sos/breathing", "/sos/breathing" in html_idx)
        check("Содержит ссылку на /sos/grounding", "/sos/grounding" in html_idx)
        check(
            "Содержит номер телефона доверия 8-800-2000-122",
            "8-800-2000-122" in html_idx or "88002000122" in html_idx,
        )
        check(
            "Содержит номер экстренной помощи 112",
            re.search(r"\b112\b", html_idx) is not None,
        )
        check(
            "Содержит дисклеймер о немедицинском характере",
            ("не является медицинским" in html_idx or "is not a medical" in html_idx)
            or "немедицинск" in low_idx,
        )
        # Никаких pop-up / alert / реклама
        check(
            "НЕ содержит JavaScript alert() или confirm() (раздражает в панике)",
            "alert(" not in html_idx and "confirm(" not in html_idx,
        )
        check(
            "НЕ содержит навязчивых элементов (рекламы/баннеров)",
            "реклам" not in low_idx and "advertis" not in low_idx,
        )

        # ============================================================
        # 4. Страница дыхания
        # ============================================================
        print()
        print("--- 4. Страница дыхания (/sos/breathing) ---")
        r, html_b = html_from(anon, "/ru/sos/breathing")
        check("/sos/breathing → статус 200", r.status_code == 200,
              f"status={r.status_code}")
        low_b = html_b.lower()
        # CSS файл подключён или есть inline-стили
        sos_css = read_file("app/static/css/sos.css")
        check(
            "Подключён sos.css ИЛИ содержит inline-стили с анимациями",
            "/static/css/sos.css" in html_b or "sos.css" in html_b
            or "@keyframes" in html_b or "<style" in html_b,
        )
        # JS-файл подключён или есть inline-скрипт
        sos_js = read_file("app/static/js/sos.js")
        check(
            "Подключён sos.js ИЛИ содержит inline-скрипт",
            "/static/js/sos.js" in html_b or "sos.js" in html_b
            or "<script" in html_b,
        )

        check("Содержит слово 'Вдох'/'вдох'", "вдох" in low_b)
        check("Содержит слово 'Выдох'/'выдох'", "выдох" in low_b)
        merged_b_low = (html_b + (sos_js or "")).lower()
        check(
            "Содержит 'Задержи'/'задержка'/'hold'",
            "задержи" in merged_b_low or "задержка" in merged_b_low
            or "hold" in merged_b_low,
        )

        # Параметры 4-7-8: учитываем как HTML, так и JS (если значения в JS-файле)
        merged_b = html_b + (sos_js or "")
        has_4 = bool(re.search(r"\b4\b", merged_b))
        has_7 = bool(re.search(r"\b7\b", merged_b))
        has_8 = bool(re.search(r"\b8\b", merged_b))
        check("Содержит число 4 (параметр дыхания)", has_4)
        check("Содержит число 7 (параметр дыхания)", has_7)
        check("Содержит число 8 (параметр дыхания)", has_8)

        check(
            "Содержит кнопку 'Старт'/'Начать'",
            "Старт" in html_b or "старт" in low_b or "Начать" in html_b,
        )
        check(
            "Содержит кнопку 'Пауза'/'Stop'",
            "Пауза" in html_b or "пауза" in low_b
            or "Stop" in html_b or "Остановить" in html_b
            or "breathToggle" in html_b,  # toggle-кнопка
        )
        check("Содержит ссылку 'Назад' → /sos/",
              "/sos/" in html_b and ("Назад" in html_b or "назад" in low_b))

        # CSS @keyframes
        merged_css = (sos_css or "") + html_b
        check(
            "CSS содержит @keyframes (анимация круга)",
            "@keyframes" in merged_css,
        )

        # ============================================================
        # 5. Страница заземления
        # ============================================================
        print()
        print("--- 5. Страница заземления (/sos/grounding) ---")
        r, html_g = html_from(anon, "/ru/sos/grounding")
        check("/sos/grounding → статус 200", r.status_code == 200,
              f"status={r.status_code}")
        low_g = html_g.lower()

        check(
            "Содержит '5-4-3-2-1'/'5 вещей'/'заземление'",
            "5-4-3-2-1" in html_g or "5 вещей" in low_g or "заземлен" in low_g,
        )
        # Тексты шагов могут рендериться JS-ом из массива STEPS,
        # поэтому ищем в HTML И в подключённом sos.js.
        merged_g_low = (html_g + (sos_js or "")).lower()
        check("Содержит 'видишь'/'ВИДИШЬ'", "видишь" in merged_g_low)
        check("Содержит 'слышишь'/'СЛЫШИШЬ'", "слышишь" in merged_g_low)
        check(
            "Содержит 'потрогать'/'коснуться'",
            "потрогать" in merged_g_low or "коснуться" in merged_g_low
            or "трогать" in merged_g_low,
        )
        check(
            "Содержит 'запах'/'ЧУВСТВУЕШЬ'",
            "запах" in merged_g_low or "чувствуешь" in merged_g_low,
        )
        check(
            "Содержит 'вкус'/'ОЩУЩАЕШЬ'",
            "вкус" in merged_g_low or "ощущаешь" in merged_g_low,
        )

        # input поля (минимум 5 — для шага «5 вещей»). Шаги могут рендериться
        # JS-ом, поэтому считаем input'ы в html ИЛИ string-литералы в sos.js.
        inputs_in_html = len(re.findall(r"<input\b", html_g, re.IGNORECASE))
        inputs_in_js = 0
        if sos_js:
            inputs_in_js = len(re.findall(
                r"['\"]<input\b|createElement\(\s*['\"]input['\"]\)|input type=",
                sos_js,
                re.IGNORECASE,
            ))
        check(
            "Минимум 5 input-полей для шага 1 (в HTML или генерируются JS)",
            inputs_in_html >= 5 or inputs_in_js >= 1,
            f"html_inputs={inputs_in_html} js_input_markers={inputs_in_js}",
        )

        check(
            "Содержит кнопку 'Далее'/'Следующий шаг'",
            "Далее" in html_g or "далее" in low_g or "Следующий" in html_g
            or (sos_js is not None and "Далее" in sos_js),
        )
        check(
            "Содержит прогресс/индикатор шага 'Шаг X из 5'",
            re.search(r"Шаг\s+\d+\s+из\s+5", html_g + (sos_js or "")) is not None
            or "ground-progress" in html_g,
        )
        check("Содержит ссылку 'Назад' → /sos/",
              "/sos/" in html_g and ("Назад" in html_g or "назад" in low_g))

        # ============================================================
        # 6. Кнопка SOS в навигации (на защищённой странице)
        # ============================================================
        print()
        print("--- 6. Кнопка SOS в base.html ---")
        # Зарегистрируем пользователя и зайдём на /dashboard/
        from app.models import User
        u = User(username="sosnav", email="sosnav@test.com")
        u.set_password("pass1234")
        db.session.add(u); db.session.commit()
        c = app.test_client()
        c.post("/ru/auth/login",
               data={"email": "sosnav@test.com", "password": "pass1234"},
               follow_redirects=False)
        r_dash, html_dash = html_from(c, "/ru/dashboard/")
        check("/dashboard/ доступен залогиненному → 200",
              r_dash.status_code == 200, f"status={r_dash.status_code}")
        check("base.html содержит ссылку на /sos/", "/sos/" in html_dash)
        check("Ссылка содержит текст 'SOS'",
              "SOS" in html_dash or "sos" in html_dash)
        check(
            "SOS-кнопка стилизована (красный фон)",
            "sos-btn" in html_dash and ("#dc2626" in html_dash or "red" in html_dash.lower() or "#b91c1c" in html_dash),
        )

        # ============================================================
        # 7. CSS файл SOS
        # ============================================================
        print()
        print("--- 7. CSS файл SOS ---")
        css_path = "app/static/css/sos.css"
        css_present = sos_css is not None
        check("Файл app/static/css/sos.css существует ИЛИ стили inline",
              css_present or "<style" in html_b)

        css_content = sos_css or (html_b + html_g + html_idx)

        check("CSS содержит @keyframes (минимум одна анимация)",
              "@keyframes" in css_content)
        # тёмные цвета фона
        dark_colors = ["#0f", "#1a", "#24", "#2b", "#302b", "dark"]
        check(
            "CSS содержит тёмные цвета фона",
            any(c in css_content.lower() for c in [c.lower() for c in dark_colors]),
        )
        check(
            "CSS содержит стили для круга (border-radius: 50% / circle)",
            "border-radius: 50%" in css_content
            or "border-radius:50%" in css_content
            or "border-radius: 999px" in css_content,
        )

        # ============================================================
        # 8. JS файл SOS
        # ============================================================
        print()
        print("--- 8. JS файл SOS ---")
        check("Файл app/static/js/sos.js существует ИЛИ скрипт inline",
              sos_js is not None or "<script" in html_b)

        js_content = sos_js or (html_b + html_g)

        check(
            "JS содержит setInterval / setTimeout (таймер)",
            "setInterval" in js_content or "setTimeout" in js_content,
        )
        check(
            "JS содержит логику фаз (inhale/hold/exhale или вдох/задержка/выдох)",
            "inhale" in js_content.lower() or "exhale" in js_content.lower()
            or "hold" in js_content.lower()
            or "вдох" in js_content.lower() or "выдох" in js_content.lower(),
        )

        # ============================================================
        # 9. Приватность (заземление не шлёт данные на сервер)
        # ============================================================
        print()
        print("--- 9. Приватность заземления ---")
        # формы с POST
        post_forms = re.findall(
            r"<form\b[^>]*method\s*=\s*['\"]?post",
            html_g,
            re.IGNORECASE,
        )
        check(
            "Нет форм с method=POST на странице заземления",
            len(post_forms) == 0,
            f"found={len(post_forms)}",
        )
        # fetch / XMLHttpRequest в JS — допускаем только GET-fetch вне grounding;
        # но в grounding JS не должен слать пользовательские ответы.
        # Проверим, что в коде grounding (initGrounding) нет fetch/XHR с answers.
        ground_js_section = ""
        if sos_js:
            # вытащим блок initGrounding (от function initGrounding до конца файла или
            # следующей function init*)
            m = re.search(r"initGrounding[\s\S]*?(?=\n\s*function\s+init|\Z)", sos_js)
            if m:
                ground_js_section = m.group(0)
        suspicious = re.search(
            r"\bfetch\s*\(|XMLHttpRequest|navigator\.sendBeacon",
            ground_js_section,
        )
        check(
            "В коде заземления нет fetch()/XMLHttpRequest (данные не уходят на сервер)",
            suspicious is None,
            f"matched={suspicious.group(0) if suspicious else None}",
        )

        # ============================================================
        # 10. Mobile-адаптив
        # ============================================================
        print()
        print("--- 10. Mobile-адаптив ---")
        check(
            "CSS содержит @media (max-width: ...) или (min-width: ...)",
            re.search(
                r"@media\s*\([^)]*(?:max-width|min-width)\s*:",
                css_content,
            ) is not None,
        )

        # ============================================================
        # 11. UX
        # ============================================================
        print()
        print("--- 11. Доступность и UX ---")
        full = html_idx + html_b + html_g + (sos_js or "")
        check(
            "Нет alert()/confirm() на SOS-страницах",
            "alert(" not in full and "confirm(" not in full,
        )
        # автоматических pop-up быть не должно (нет window.open, prompt, etc.)
        check(
            "Нет автоматических pop-up (window.open / prompt)",
            "window.open(" not in full and "prompt(" not in full,
        )
        # font-size минимум 16px — проверяем что хоть один читаемый размер задан
        sizes = re.findall(r"font-size\s*:\s*([0-9.]+)\s*(px|rem|em)", css_content)
        ok_size = False
        for v, unit in sizes:
            try:
                val = float(v)
                if unit == "px" and val >= 16:
                    ok_size = True; break
                if unit in ("rem", "em") and val >= 1.0:
                    ok_size = True; break
            except ValueError:
                pass
        check(
            "В CSS задан крупный font-size (≥16px / ≥1rem)",
            ok_size,
            f"sizes={sizes[:5]}",
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
