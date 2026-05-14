"""
test_module9.py — тестирование модуля 9 (советы и техники).
Запуск: python test_module9.py
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


def html_from(client, url):
    r = client.get(url, headers={"Accept": "text/html"}, follow_redirects=False)
    return r, r.data.decode("utf-8", errors="replace")


def has_cyrillic(s: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", s or ""))


def run_checks():
    from app import create_app

    app = create_app("testing")

    print("=" * 60)
    print("=== ТЕСТИРОВАНИЕ МОДУЛЯ 9: СОВЕТЫ И ТЕХНИКИ ===")
    print("=" * 60)
    print()

    with app.app_context():
        c = app.test_client()

        # ============================================================
        # 1. Blueprint и маршруты
        # ============================================================
        print("--- 1. Blueprint и маршруты ---")
        check("Blueprint tips зарегистрирован", "tips" in app.blueprints)

        rules = [str(r.rule) for r in app.url_map.iter_rules()]
        check("URL /tips/ существует", "/tips/" in rules,
              f"tips rules={[r for r in rules if r.startswith('/tips')]}")
        check(
            "URL /tips/<id> или /tips/<slug> существует",
            any(r.startswith("/tips/") and ("<" in r) for r in rules),
            f"rules={[r for r in rules if r.startswith('/tips')]}",
        )

        # ============================================================
        # 2. Доступность без авторизации
        # ============================================================
        print()
        print("--- 2. Доступность БЕЗ авторизации ---")
        r, _ = html_from(c, "/ru/tips/")
        check("/tips/ БЕЗ токена → 200", r.status_code == 200,
              f"status={r.status_code} loc={r.headers.get('Location')}")

        r, _ = html_from(c, "/ru/tips/1")
        check("/tips/1 БЕЗ токена → 200", r.status_code == 200,
              f"status={r.status_code}")

        # ============================================================
        # 3. Список техник
        # ============================================================
        print()
        print("--- 3. Список техник (/tips/) ---")
        r, html_idx = html_from(c, "/ru/tips/")
        check("/tips/ статус 200", r.status_code == 200, f"status={r.status_code}")

        # Карточки
        cards = re.findall(r"tip-card", html_idx)
        check(
            "Минимум 6 карточек техник",
            len(cards) >= 6,
            f"found tip-card occurrences={len(cards)}",
        )

        for needle, label in [
            ("4-7-8", "Дыхание 4-7-8"),
            ("реструктуризация", "Когнитивная реструктуризация"),
        ]:
            check(
                f"Содержит '{label}'",
                needle.lower() in html_idx.lower(),
            )

        check(
            "Содержит 'Прогрессивная мышечная релаксация' / 'PMR'",
            "мышечная релаксация" in html_idx.lower() or "PMR" in html_idx
            or "релаксаци" in html_idx.lower(),
        )
        check(
            "Содержит 'Заземление' / '5-4-3-2-1'",
            "заземлен" in html_idx.lower() or "5-4-3-2-1" in html_idx,
        )
        check(
            "Содержит 'Наихудший сценарий'",
            "наихудш" in html_idx.lower() or "худший" in html_idx.lower(),
        )
        check(
            "Содержит 'Позитивная визуализация'",
            "визуализаци" in html_idx.lower(),
        )
        check(
            "Содержит 'Подробнее' или ссылки на детальные страницы",
            "Подробнее" in html_idx or re.search(r"href=\"/tips/\d+", html_idx) is not None
            or re.search(r"href=\"/tips/[a-z0-9\-]+", html_idx) is not None,
        )

        # ============================================================
        # 4. Категории
        # ============================================================
        print()
        print("--- 4. Категории ---")
        check("Содержит категорию 'Дыхание'", "Дыхание" in html_idx)
        check("Содержит категорию 'Когниция'",
              "Когниция" in html_idx or "когниц" in html_idx.lower())
        check("Содержит категорию 'Тело'", "Тело" in html_idx)

        # фильтр-кнопки
        has_filter = (
            "tip-filter" in html_idx
            or 'data-category="all"' in html_idx
            or re.search(r'class="[^"]*filter[^"]*"', html_idx) is not None
        )
        check("Есть кнопки/табы фильтра", has_filter)
        check(
            "Карточки имеют атрибут data-category",
            'data-category="breathing"' in html_idx
            or 'data-category="cognition"' in html_idx
            or 'data-category="body"' in html_idx,
        )

        # ============================================================
        # 5. Детальная страница техники
        # ============================================================
        print()
        print("--- 5. Детальная страница (/tips/1) ---")
        r, html_d = html_from(c, "/ru/tips/1")
        check("/tips/1 статус 200", r.status_code == 200, f"status={r.status_code}")

        # tip 1 = "Дыхание 4-7-8"
        check("Содержит название техники ('4-7-8')", "4-7-8" in html_d)

        # описание ≥ 50 символов: ищем секцию описания
        # хорошо проверить просто наличие длинного куска кириллического текста
        cyr_chunks = re.findall(r"[А-Яа-яЁё][А-Яа-яЁё \-,.;:«»()\d]{49,}", html_d)
        check(
            "Содержит описание длиной ≥ 50 символов",
            len(cyr_chunks) > 0,
            f"max chunk len={max((len(s) for s in cyr_chunks), default=0)}",
        )

        check(
            "Содержит 'Когда использовать'",
            "Когда использовать" in html_d or "когда использовать" in html_d.lower(),
        )

        # шаги — должны быть ≥ 4 элементов <li>
        li_in_steps = len(re.findall(r"<li\b", html_d, re.IGNORECASE))
        check(
            "Содержит пошаговую инструкцию (≥ 4 <li>)",
            li_in_steps >= 4,
            f"<li> count={li_in_steps}",
        )

        check(
            "Содержит бейдж сложности ('Лёгкая' / 'Средняя')",
            "Лёгкая" in html_d or "Средняя" in html_d,
        )
        check(
            "Содержит время выполнения (минуты)",
            "мин" in html_d.lower(),
        )
        check("Содержит ссылку назад на /tips/", "/tips/" in html_d)

        # ============================================================
        # 6. Каждая техника
        # ============================================================
        print()
        print("--- 6. Перебор всех техник 1..9 ---")
        from app.data.tips_data import TIPS

        for tip in TIPS:
            tid = tip["id"]
            r, html_t = html_from(c, f"/tips/{tid}")
            check(f"/tips/{tid} → 200", r.status_code == 200,
                  f"status={r.status_code}")
            check(f"/tips/{tid}: непустое название", bool(tip["title"].strip()))
            check(
                f"/tips/{tid}: инструкция содержит ≥ 3 шагов",
                len(tip.get("steps", [])) >= 3,
                f"steps={len(tip.get('steps', []))}",
            )
            check(
                f"/tips/{tid}: категория одна из breathing/cognition/body",
                tip["category"] in ("breathing", "cognition", "body"),
                f"got={tip['category']!r}",
            )

        # ============================================================
        # 7. Несуществующие техники
        # ============================================================
        print()
        print("--- 7. Несуществующая техника ---")
        r = c.get("/ru/tips/999", headers={"Accept": "text/html"})
        check("/tips/999 → 404", r.status_code == 404, f"status={r.status_code}")
        r = c.get("/ru/tips/abc", headers={"Accept": "text/html"})
        check("/tips/abc (несуществующий slug) → 404",
              r.status_code == 404, f"status={r.status_code}")

        # ============================================================
        # 8. Контент техник — правильность CBT
        # ============================================================
        print()
        print("--- 8. Корректность CBT-контента ---")

        def html_for(slug_or_id):
            r, h = html_from(c, f"/ru/tips/{slug_or_id}")
            return h if r.status_code == 200 else ""

        h_478 = html_for(1)  # Дыхание 4-7-8
        check(
            "Техника 'Дыхание 4-7-8' содержит числа 4, 7, 8",
            "4" in h_478 and "7" in h_478 and "8" in h_478
            and "4-7-8" in h_478,
        )

        h_grd = html_for("grounding-54321")
        if not h_grd:
            h_grd = html_for(8)
        check(
            "Техника 'Заземление 5-4-3-2-1' содержит 'видите'/'видишь' и 'слышите'/'слышишь'",
            (
                ("видите" in h_grd.lower() or "видишь" in h_grd.lower())
                and ("слышите" in h_grd.lower() or "слышишь" in h_grd.lower())
            ),
        )

        h_cog = html_for(4)  # Когнитивная реструктуризация
        check(
            "Техника 'Когнитивная реструктуризация' содержит 'когнитивное искажение' / 'негативн'",
            "когнитивное искажение" in h_cog.lower()
            or "негативн" in h_cog.lower(),
        )

        h_pmr = html_for(7)  # PMR
        check(
            "Техника 'Мышечная релаксация' содержит 'напряг' и 'расслаб'",
            "напряг" in h_pmr.lower() and "расслаб" in h_pmr.lower(),
        )

        h_worst = html_for(5)
        check(
            "Техника 'Наихудший сценарий' содержит 'худшее' / 'наихудш'",
            "худшее" in h_worst.lower() or "наихудш" in h_worst.lower(),
        )

        h_vis = html_for(9)
        check(
            "Техника 'Визуализация' содержит 'представ' (представьте)",
            "представ" in h_vis.lower(),
        )

        # ============================================================
        # 9. Ссылки на SOS
        # ============================================================
        print()
        print("--- 9. Ссылки на SOS ---")
        check(
            "Техника дыхания (1) содержит ссылку на /sos/breathing или /sos/",
            "/sos/breathing" in h_478 or "/sos/" in h_478,
        )
        check(
            "Техника заземления (8) содержит ссылку на /sos/grounding или /sos/",
            "/sos/grounding" in h_grd or "/sos/" in h_grd,
        )

        # ============================================================
        # 10. CSS и JS
        # ============================================================
        print()
        print("--- 10. CSS и JS файлы ---")
        css = read_file("app/static/css/tips.css")
        js = read_file("app/static/js/tips.js")
        css_or_inline = css if css is not None else (
            html_idx if "<style" in html_idx else ""
        )
        js_or_inline = js if js is not None else (
            html_idx if "<script" in html_idx else ""
        )

        check("Файл app/static/css/tips.css существует ИЛИ inline-стили",
              css is not None or "<style" in html_idx)

        check(
            "CSS содержит grid или flex (сетка карточек)",
            "grid" in (css_or_inline or "") or "flex" in (css_or_inline or ""),
        )
        check(
            "CSS содержит border-radius (скруглённые карточки)",
            "border-radius" in (css_or_inline or ""),
        )
        check(
            "CSS содержит @media (адаптив)",
            re.search(r"@media\s*\([^)]*(?:max-width|min-width)\s*:",
                      css_or_inline or "") is not None,
        )

        check("Файл app/static/js/tips.js существует ИЛИ скрипт inline",
              js is not None or "<script" in html_idx)
        check(
            "JS содержит функцию фильтрации (filter/category/addEventListener)",
            ("filter" in (js_or_inline or "").lower()
             or "category" in (js_or_inline or "").lower()
             or "addEventListener" in (js_or_inline or "")),
        )

        # ============================================================
        # 11. Навигация (наследование base.html)
        # ============================================================
        print()
        print("--- 11. Навигация ---")
        check(
            "Страница tips наследует base.html (есть логотип/класс navbar)",
            "navbar" in html_idx or "SocialHealth" in html_idx,
        )
        check(
            "Навигация содержит ссылку на /tips/ или 'Советы'",
            'href="/tips/' in html_idx or "Советы" in html_idx,
        )

        # ============================================================
        # 12. Тексты на русском
        # ============================================================
        print()
        print("--- 12. Тексты на русском ---")
        for tip in TIPS:
            joined = " ".join(
                [
                    tip.get("title", ""),
                    tip.get("description", ""),
                    tip.get("when_to_use", ""),
                ]
                + [
                    s if isinstance(s, str) else (
                        s.get("text", "") + " "
                        + " ".join(s.get("sub", []) or [])
                    )
                    for s in tip.get("steps", [])
                ]
            )
            check(
                f"Техника '{tip['title']}' содержит кириллицу",
                has_cyrillic(joined),
            )

        # бейджи на русском
        check(
            "Бейдж сложности на русском ('Лёгкая' или 'Средняя')",
            "Лёгкая" in html_idx or "Средняя" in html_idx,
        )
        check(
            "Нет английских бейджей 'Easy'/'Medium'",
            ">Easy<" not in html_idx and ">Medium<" not in html_idx
            and ">Hard<" not in html_idx,
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
