from __future__ import annotations

from dataclasses import dataclass

from ..models import NewsEvent
from ..services.messaging import RabbitMQTopicClient


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
        # TODO: wrap the event into an OutboxMessage and append it to self._messages
        raise NotImplementedError

    def pending(self) -> list[OutboxMessage]:
        # TODO: return only messages where published is False
        raise NotImplementedError

    def mark_published(self, message_id: str) -> None:
        # TODO: find the message by id and set published = True
        raise NotImplementedError


class OutboxPublisher:
    def __init__(self, outbox: InMemoryOutbox, broker: RabbitMQTopicClient) -> None:
        self._outbox = outbox
        self._broker = broker

    def publish_pending(self) -> list[OutboxMessage]:
        # TODO: iterate over pending messages, publish each one via self._broker,
        # mark it published, and return the list of published messages
        raise NotImplementedError