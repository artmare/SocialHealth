"""Тесты AIService — все с mock, без обращения к реальному API."""

import json
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from app.services.ai_service import AIService


def _fake_response(text: str):
    """Эмулирует структуру anthropic-ответа: response.content[0].text."""
    return SimpleNamespace(content=[SimpleNamespace(text=text)])


def test_analyze_entry_no_api_key(app):
    """Без ключа → fallback-плейсхолдер, не падает."""
    with app.app_context():
        with patch.object(AIService, "_get_client", return_value=None):
            result = AIService.analyze_entry("текст", anxiety_level=5)
    assert isinstance(result, dict)
    for key in ("summary", "insight", "recommendation"):
        assert key in result
        assert isinstance(result[key], str)


def test_analyze_entry_success(app):
    """Mock API возвращает валидный JSON → парсится корректно."""
    with app.app_context():
        fake_client = MagicMock()
        fake_client.messages.create.return_value = _fake_response(json.dumps({
            "summary": "Резюме",
            "insight": "Катастрофизация",
            "recommendation": "Дыхание 4-7-8",
        }))
        with patch.object(AIService, "_get_client", return_value=fake_client):
            result = AIService.analyze_entry("test", anxiety_level=6)
    assert result["summary"] == "Резюме"
    assert result["insight"] == "Катастрофизация"
    assert result["recommendation"] == "Дыхание 4-7-8"


def test_analyze_entry_json_error(app):
    """API возвращает не-JSON → fallback, не падает."""
    with app.app_context():
        fake_client = MagicMock()
        fake_client.messages.create.return_value = _fake_response("Это не JSON, просто текст.")
        with patch.object(AIService, "_get_client", return_value=fake_client):
            result = AIService.analyze_entry("t", 5)
    assert isinstance(result, dict)
    assert "summary" in result


def test_analyze_entry_api_error(app):
    """API бросает Exception → fallback, не падает."""
    with app.app_context():
        fake_client = MagicMock()
        fake_client.messages.create.side_effect = RuntimeError("network down")
        with patch.object(AIService, "_get_client", return_value=fake_client):
            result = AIService.analyze_entry("t", 5)
    assert isinstance(result, dict)
    assert all(k in result for k in ("summary", "insight", "recommendation"))


def test_weekly_report_success(app):
    with app.app_context():
        fake_client = MagicMock()
        fake_client.messages.create.return_value = _fake_response(json.dumps({
            "trend": "падает",
            "patterns": "общение в больших группах",
            "progress": "стало легче говорить с коллегами",
            "next_week_focus": "практика 4-7-8 утром",
        }))
        with patch.object(AIService, "_get_client", return_value=fake_client):
            result = AIService.generate_weekly_report("данные за неделю")
    for k in ("trend", "patterns", "progress", "next_week_focus"):
        assert k in result and isinstance(result[k], str) and len(result[k]) > 0


def test_weekly_report_no_api_key(app):
    with app.app_context():
        with patch.object(AIService, "_get_client", return_value=None):
            result = AIService.generate_weekly_report("...")
    for k in ("trend", "patterns", "progress", "next_week_focus"):
        assert k in result


def test_analysis_prompt_contains_rules():
    """Системный промпт упоминает CBT, JSON-формат и помощь специалиста при 9-10/10."""
    p = AIService.ANALYSIS_PROMPT
    assert "CBT" in p or "когнитив" in p.lower()
    assert "JSON" in p or "json" in p
    assert "9" in p and "10" in p
    assert "8-800-2000-122" in p
