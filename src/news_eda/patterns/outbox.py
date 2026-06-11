from __future__ import annotations

from dataclasses import dataclass

from ..models import NewsEvent
from ..services.faulty_client import FaultyRabbitClient


@dataclass
class OutboxMessage:
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
                id=event.id,
                topic=event.topic,
                payload=event.to_json(),
            )
        )

    def pending(self) -> list[OutboxMessage]:
        return [message for message in self._messages if not message.published]

    def mark_published(self, message_id: str) -> None:
        for message in self._messages:
            if message.id == message_id:
                message.published = True
                return


class OutboxPublisher:
    def __init__(self, outbox: InMemoryOutbox, broker: FaultyRabbitClient) -> None:
        self._outbox = outbox
        self._broker = broker

    def publish_pending(self, *, index: int) -> list[OutboxMessage]:
        published_messages: list[OutboxMessage] = []

        for message in self._outbox.pending():
            was_published = self._broker.publish(
                routing_key=message.topic,
                message=message.payload,
                index=index,
            )

            if was_published:
                self._outbox.mark_published(message.id)
                published_messages.append(message)

        return published_messages