from __future__ import annotations

from .gemini_client import GeminiNewsGenerator
from .messaging import RabbitMQTopicClient
from ..models import NewsEvent


class FantasyNewsProducer:
    def __init__(self, generator: GeminiNewsGenerator, broker: RabbitMQTopicClient) -> None:
        self._generator = generator
        self._broker = broker

    def create_event(self, topic: str) -> NewsEvent:
        article = self._generator.generate(topic)
        return NewsEvent.create(
            topic=topic,
            title=article["title"],
            body=article["body"],
            source=article["source"],
        )

    def publish_event(self, event: NewsEvent) -> None:
        self._broker.publish(routing_key=event.topic, message=event.to_json())

    def generate_and_publish(self, topic: str) -> NewsEvent:
        event = self.create_event(topic)
        self.publish_event(event)
        return event
