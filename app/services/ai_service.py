import json
import os
from typing import Optional

from flask import current_app


class AIService:
    @staticmethod
    def analyze_entry(text: str, anxiety_level: int) -> dict:
        """
        Отправляет текст дневника в Anthropic Claude API.
        При отсутствии API-ключа возвращает placeholder.
        """
        api_key = current_app.config.get("ANTHROPIC_API_KEY") or os.environ.get(
            "ANTHROPIC_API_KEY"
        )

        if not api_key:
            return AIService._placeholder_response(anxiety_level)

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            system_prompt = (
                "Ты — поддерживающий CBT-терапевт. "
                "Проанализируй запись человека, страдающего социальной тревожностью. "
                "Ответь строго в JSON формате с тремя ключами: "
                "summary (краткое резюме ситуации), "
                "insight (обнаруженные когнитивные искажения или паттерны мышления), "
                "recommendation (конкретная рекомендация для преодоления тревоги). "
                "Все значения — строки на русском языке."
            )

            if anxiety_level >= 9:
                system_prompt += (
                    " ВАЖНО: уровень тревоги очень высокий (9-10 из 10). "
                    "Обязательно порекомендуй обратиться к профессиональному психотерапевту."
                )

            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=512,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"Уровень тревоги: {anxiety_level}/10.\nТекст: {text}",
                    }
                ],
            )

            raw = response.content[0].text.strip()
            # Попробуем извлечь JSON из markdown code block
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("\n", 1)[0]
                if raw.startswith("json"):
                    raw = raw[4:].strip()

            parsed = json.loads(raw)
            return {
                "summary": str(parsed.get("summary", "")),
                "insight": str(parsed.get("insight", "")),
                "recommendation": str(parsed.get("recommendation", "")),
            }
        except Exception:
            return AIService._placeholder_response(anxiety_level)

    @staticmethod
    def _placeholder_response(anxiety_level: int) -> dict:
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
                "обратиться к квалифицированному специалисту."
            )
        return {
            "summary": summary,
            "insight": insight,
            "recommendation": recommendation,
        }
