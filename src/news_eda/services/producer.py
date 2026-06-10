from __future__ import annotations

from ..patterns.outbox import InMemoryOutbox
from .gemini_client import GeminiNewsGenerator
from ..models import NewsEvent


class FantasyNewsProducer:
    def __init__(self, generator: GeminiNewsGenerator, outbox: InMemoryOutbox) -> None:
        self._generator = generator
        self._outbox = outbox

    def create_event(self, topic: str) -> NewsEvent:
        article = self._generator.generate(topic)
        event = NewsEvent.create(
            topic=topic,
            title=article["title"],
            body=article["body"],
            source=article["source"],
        )
        self._outbox.add_event(event)
        return event

    def generate_and_publish(self, topic: str) -> NewsEvent:
        event = self.create_event(topic)
        return event
