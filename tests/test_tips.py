"""Тесты библиотеки CBT-техник."""


def test_tips_no_auth_required(client):
    r = client.get("/tips/", headers={"Accept": "text/html"}, follow_redirects=False)
    assert r.status_code == 200


def test_tips_list_content(client):
    body = client.get("/tips/", headers={"Accept": "text/html"}).data.decode("utf-8")
    cards = body.count("tip-card")
    assert cards >= 6
    # хотя бы некоторые из ключевых техник
    assert "4-7-8" in body
    assert (
        "реструктуризация" in body.lower()
        or "когнитивн" in body.lower()
        or "cognitive" in body.lower()
        or "restructuring" in body.lower()
    )


def test_tips_detail(client):
    r = client.get("/tips/1", headers={"Accept": "text/html"})
    assert r.status_code == 200
    body = r.data.decode("utf-8")
    assert "4-7-8" in body
    # Шаги — нумерованный список (>=4 <li>)
    assert body.lower().count("<li") >= 4


def test_tips_not_found(client):
    r = client.get("/tips/999", headers={"Accept": "text/html"})
    assert r.status_code == 404
