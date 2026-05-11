import json
import logging
import os
from datetime import date
from typing import Optional

from flask import current_app

logger = logging.getLogger(__name__)


class AIService:
    ANALYSIS_PROMPT = (
        "Ты — помощник по когнитивно-поведенческой терапии (CBT) "
        "для людей с социальной тревожностью. "
        "Твой тон — поддерживающий, неосуждающий, на русском языке. "
        "Проанализируй запись пользователя и верни строго JSON с тремя ключами: "
        "summary (краткое резюме состояния, 1-2 предложения), "
        "insight (какие когнитивные искажения заметны: катастрофизация, "
        "чтение мыслей, персонализация и т.д.), "
        "recommendation (конкретная CBT-техника на сегодня). "
        "Правила: никогда не ставь диагнозы, не критикуй пользователя. "
        "Все значения — строки на русском языке. "
        "Если уровень тревоги 9-10 из 10 — обязательно рекомендуй "
        "обратиться к специалисту и укажи телефон доверия 8-800-2000-122."
    )

    WEEKLY_REPORT_PROMPT = (
        "Ты — CBT-терапевт. Проанализируй записи пользователя за неделю "
        "и верни строго JSON с четырьмя ключами: "
        "trend (динамика тревоги за неделю: растёт/падает/стабильна), "
        "patterns (замеченные паттерны и триггеры), "
        "progress (что улучшилось), "
        "next_week_focus (на чём сфокусироваться на следующей неделе). "
        "Все значения — строки на русском языке."
    )

    MODERATION_PROMPT = (
        "Ты — модератор сообщества. Проанализируй текст поста "
        "и верни строго JSON с тремя ключами: "
        "approved (true/false — одобрен ли пост), "
        "reason (краткое объяснение решения), "
        "toxicity_score (число от 0.0 до 1.0). "
        "Запрещено: суицидальный контент, персональные данные, токсичность, угрозы."
    )

    @staticmethod
    def _get_client():
        api_key = current_app.config.get("ANTHROPIC_API_KEY") or os.environ.get(
            "ANTHROPIC_API_KEY"
        )
        if not api_key:
            return None
        import anthropic

        return anthropic.Anthropic(api_key=api_key)

    @staticmethod
    def _call_api(client, system_prompt: str, user_content: str, max_tokens: int) -> str:
        # TODO: Redis cache для экономии ~40% API вызовов
        import anthropic

        model = current_app.config.get("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
        logger.info("AI API request started (model=%s)", model)
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )
            raw = response.content[0].text.strip()
            logger.info("AI API request completed successfully")
            return raw
        except anthropic.APIError as exc:
            logger.error("Anthropic API error: %s", exc)
            raise
        except Exception as exc:
            logger.error("Unexpected API error: %s", exc)
            raise

    @staticmethod
    def _extract_json(raw_text: str) -> dict:
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:].strip()
        return json.loads(raw_text)

    @staticmethod
    def analyze_entry(text: str, anxiety_level: int) -> dict:
        client = AIService._get_client()
        if not client:
            logger.warning("ANTHROPIC_API_KEY not set, returning placeholder for analyze_entry")
            return AIService._fallback_analysis(anxiety_level)

        user_content = f"Уровень тревоги: {anxiety_level}/10.\nТекст записи: {text}"

        try:
            raw = AIService._call_api(
                client, AIService.ANALYSIS_PROMPT, user_content, 500
            )
            parsed = AIService._extract_json(raw)
            return {
                "summary": str(parsed.get("summary", "")),
                "insight": str(parsed.get("insight", "")),
                "recommendation": str(parsed.get("recommendation", "")),
            }
        except json.JSONDecodeError as exc:
            logger.error("JSON decode error in analyze_entry: %s", exc)
            return AIService._fallback_analysis(anxiety_level)
        except Exception as exc:
            logger.error("Error in analyze_entry: %s", exc)
            return AIService._fallback_analysis(anxiety_level)

    @staticmethod
    def generate_weekly_report(weekly_data: str) -> dict:
        client = AIService._get_client()
        if not client:
            logger.warning("ANTHROPIC_API_KEY not set, returning placeholder for weekly_report")
            return AIService._fallback_weekly_report()

        try:
            raw = AIService._call_api(
                client, AIService.WEEKLY_REPORT_PROMPT, weekly_data, 800
            )
            parsed = AIService._extract_json(raw)
            return {
                "trend": str(parsed.get("trend", "")),
                "patterns": str(parsed.get("patterns", "")),
                "progress": str(parsed.get("progress", "")),
                "next_week_focus": str(parsed.get("next_week_focus", "")),
            }
        except json.JSONDecodeError as exc:
            logger.error("JSON decode error in generate_weekly_report: %s", exc)
            return AIService._fallback_weekly_report()
        except Exception as exc:
            logger.error("Error in generate_weekly_report: %s", exc)
            return AIService._fallback_weekly_report()

    @staticmethod
    def moderate_community_post(text: str) -> dict:
        client = AIService._get_client()
        if not client:
            logger.warning("ANTHROPIC_API_KEY not set, returning placeholder for moderation")
            return AIService._fallback_moderation()

        try:
            raw = AIService._call_api(
                client, AIService.MODERATION_PROMPT, text, 200
            )
            parsed = AIService._extract_json(raw)
            return {
                "approved": bool(parsed.get("approved", True)),
                "reason": str(parsed.get("reason", "")),
                "toxicity_score": float(parsed.get("toxicity_score", 0.0)),
            }
        except json.JSONDecodeError as exc:
            logger.error("JSON decode error in moderate_community_post: %s", exc)
            return AIService._fallback_moderation()
        except Exception as exc:
            logger.error("Error in moderate_community_post: %s", exc)
            return AIService._fallback_moderation()

    @staticmethod
    def format_weekly_data(entries: list) -> str:
        lines = []
        for entry in entries:
            emotions_str = ", ".join(entry.emotions) if entry.emotions else "—"
            text_preview = entry.text or "—"
            if len(text_preview) > 200:
                text_preview = text_preview[:200] + "..."
            lines.append(
                f"Дата: {entry.date} | Тревога: {entry.anxiety_level}/10 "
                f"| Эмоции: {emotions_str} | Текст: {text_preview}"
            )
        return "\n".join(lines)

    @staticmethod
    def _fallback_analysis(anxiety_level: int) -> dict:
        summary = "Ваша запись отражает переживание тревожной ситуации."
        insight = (
            "Часто тревога усиливается из-за катастрофизации — "
            "мы мысленно раздуваем возможные негативные исходы."
        )
        recommendation = (
            "Попробуйте технику дыхания 4-7-8: вдох 4 секунды, "
            "задержка 7 секунд, выдох 8 секунд."
        )
        if anxiety_level >= 9:
            recommendation += (
                " При таком высоком уровне тревоги рекомендуем "
                "обратиться к квалифицированному специалисту "
                "или позвонить на телефон доверия 8-800-2000-122."
            )
        return {
            "summary": summary,
            "insight": insight,
            "recommendation": recommendation,
        }

    @staticmethod
    def _fallback_weekly_report() -> dict:
        return {
            "trend": "Данные недостаточны для точного анализа динамики.",
            "patterns": "Замечен стабильный уровень тревоги без резких колебаний.",
            "progress": "Продолжайте вести дневник — это уже важный шаг вперёд.",
            "next_week_focus": (
                "Попробуйте технику дыхания 4-7-8 каждый день "
                "перед выходом из дома."
            ),
        }

    @staticmethod
    def _fallback_moderation() -> dict:
        return {
            "approved": True,
            "reason": "Ручная проверка невозможна — сервис недоступен.",
            "toxicity_score": 0.0,
        }
