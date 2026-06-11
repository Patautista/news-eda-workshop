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
        # TODO: add the event to the outbox
        return event
