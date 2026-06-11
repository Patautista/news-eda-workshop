from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class RabbitMQSettings:
    host: str = os.getenv("RABBITMQ_HOST", "localhost")
    port: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    user: str = os.getenv("RABBITMQ_USER", "guest")
    password: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    vhost: str = os.getenv("RABBITMQ_VHOST", "/")
    exchange: str = os.getenv("RABBITMQ_EXCHANGE", "fantasy.news.topic")


@dataclass(frozen=True)
class GeminiSettings:
    api_key: str = os.getenv("GEMINI_API_KEY", "")
    model: str = os.getenv("GEMINI_MODEL", "gemini-3.0-flash")
    language: str = os.getenv("GEMINI_LANGUAGE", "english")


@dataclass(frozen=True)
class AppSettings:
    rabbitmq: RabbitMQSettings = RabbitMQSettings()
    gemini: GeminiSettings = GeminiSettings()
