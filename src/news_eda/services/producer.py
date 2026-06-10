from __future__ import annotations

from .gemini_client import GeminiNewsGenerator
from .messaging import RabbitMQTopicClient
from ..models import NewsEvent


class FantasyNewsProducer:
    def __init__(self, generator: GeminiNewsGenerator, broker: RabbitMQTopicClient) -> None:
        self._generator = generator
        self._broker = broker

    def generate_and_publish(self, topic: str) -> NewsEvent:
        article = self._generator.generate(topic)
        event = NewsEvent.create(
            topic=topic,
            title=article["title"],
            body=article["body"],
            source=article["source"],
        )
        self._broker.publish(routing_key=topic, message=event.to_json())
        return event
