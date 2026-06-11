from __future__ import annotations

from dataclasses import dataclass
import random
import time
from uuid import uuid4

from ..models import NewsEvent
from ..services.messaging import RabbitMQTopicClient


@dataclass
class OutboxMessage:
    entry_id: str
    id: str
    topic: str
    payload: str
    published: bool = False


class InMemoryOutbox:
    def __init__(self) -> None:
        self._messages: list[OutboxMessage] = []

    def add_event(self, event: NewsEvent) -> None:
        self._messages.append(
            OutboxMessage(
                entry_id=str(uuid4()),
                id=event.id,
                topic=event.topic,
                payload=event.to_json(),
            )
        )

    def pending(self) -> list[OutboxMessage]:
        return [message for message in self._messages if not message.published]

    def mark_published(self, entry_id: str) -> None:
        for message in self._messages:
            if message.entry_id == entry_id:
                message.published = True
                return


class OutboxPublisher:
    def __init__(self, outbox: InMemoryOutbox, broker: RabbitMQTopicClient) -> None:
        self._outbox = outbox
        self._broker = broker

    def maybe_drop_message(self, *, drop_chance: float, event: NewsEvent, index: int, interval: float) -> bool:
        # Simulate producer-side loss: event stays in outbox for later recovery.
        if random.random() < drop_chance:
            print(
                "Queued in outbox without publish attempt: "
                f"seq={index} topic={event.topic} id={event.id} title={event.title}"
            )
            time.sleep(interval)
            return True
        return False

    def publish_pending(self) -> list[OutboxMessage]:
        published_messages: list[OutboxMessage] = []

        for message in self._outbox.pending():
            self._broker.publish(routing_key=message.topic, message=message.payload)

            self._outbox.mark_published(message.entry_id)
            published_messages.append(message)

        return published_messages