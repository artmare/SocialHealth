def test_uk_locale_prefix_renders_ukrainian(client):
    body = client.get("/uk/auth/login", headers={"Accept": "text/html"}).data.decode(
        "utf-8"
    )
    assert "Увійти" in body


def test_ru_locale_uses_improved_copy(client):
    body = client.get("/ru/auth/login", headers={"Accept": "text/html"}).data.decode(
        "utf-8"
    )
    assert "Войти" in body


def test_language_switcher_lists_ukrainian(client):
    body = client.get("/uk/auth/register", headers={"Accept": "text/html"}).data.decode(
        "utf-8"
    )
    assert 'href="/uk/auth/register"' in body


def test_profile_settings_accepts_ukrainian(auth_client):
    response = auth_client.post(
        "/profile/settings",
        data={"language": "uk", "daily_reminder_time": ""},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/uk/profile/settings")


def test_all_seed_tasks_have_ukrainian_text():
    from app.task_i18n import UK_TASK_TEXT
    from seed_tasks import TASKS

    titles = {task["title_en"] for task in TASKS}
    assert titles <= set(UK_TASK_TEXT)
