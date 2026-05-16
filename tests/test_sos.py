"""Тесты SOS-режима."""


def test_sos_no_auth_required(client):
    r = client.get("/sos/", headers={"Accept": "text/html"}, follow_redirects=False)
    assert r.status_code == 200


def test_sos_breathing_no_auth(client):
    r = client.get("/sos/breathing", headers={"Accept": "text/html"})
    assert r.status_code == 200


def test_sos_grounding_no_auth(client):
    r = client.get("/sos/grounding", headers={"Accept": "text/html"})
    assert r.status_code == 200


def test_sos_contains_helpline(client):
    body = client.get("/sos/").data.decode("utf-8")
    assert "116 123" in body or "116123" in body


def test_sos_contains_emergency(client):
    body = client.get("/sos/").data.decode("utf-8")
    assert "112" in body
