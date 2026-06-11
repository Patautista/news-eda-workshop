from __future__ import annotations

import random

from ..patterns.outbox import InMemoryOutbox
from .gemini_client import GeminiNewsGenerator
from ..models import NewsEvent


class FantasyNewsProducer:
    def __init__(self, generator: GeminiNewsGenerator, outbox: InMemoryOutbox) -> None:
        self._generator = generator
        self._outbox = outbox

    def maybe_create_duplicate(self, *, duplicate_chance: float, event: NewsEvent) -> bool:
        # Simulate at-least-once delivery by optionally queueing a duplicate event.
        if random.random() < duplicate_chance:
            self._outbox.add_event(event)
            return True
        return False

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
