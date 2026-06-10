from __future__ import annotations

import json
import random
import re

import google.generativeai as genai

from ..config import GeminiSettings


class GeminiNewsGenerator:
    def __init__(self, settings: GeminiSettings) -> None:
        self._settings = settings
        self._model = None
        if settings.api_key:
            genai.configure(api_key=settings.api_key)
            self._model = genai.GenerativeModel(settings.model)

    def generate(self, topic: str) -> dict[str, str]:
        if self._model is None:
            return self._fallback(topic)

        prompt = (
            "Create one short fictional news item in valid JSON with keys "
            'title, body, source. Topic: "'
            + topic
            + '". Keep it family-safe and under 90 words in the body.'
        )

        response = self._model.generate_content(prompt)
        text = (response.text or "").strip()

        try:
            return self._extract_json(text)
        except (ValueError, json.JSONDecodeError, KeyError):
            return self._fallback(topic)

    @staticmethod
    def _extract_json(text: str) -> dict[str, str]:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("Gemini response did not contain JSON.")

        data = json.loads(match.group(0))
        return {
            "title": str(data["title"]),
            "body": str(data["body"]),
            "source": str(data["source"]),
        }

    @staticmethod
    def _fallback(topic: str) -> dict[str, str]:
        leads = [
            "Skyships",
            "Guild envoys",
            "Clockwork ravens",
            "Crystal seers",
            "Harbor alchemists",
        ]
        actions = [
            "brokered a truce",
            "discovered a hidden passage",
            "announced a moonlit tournament",
            "unveiled a floating market",
            "mapped a storm corridor",
        ]
        lead = random.choice(leads)
        action = random.choice(actions)
        return {
            "title": f"{lead} in {topic.replace('.', ' ').title()}",
            "body": f"In a surprising turn, {lead.lower()} {action}. Witnesses say the event could reshape alliances by dawn.",
            "source": "The Mythic Ledger",
        }
