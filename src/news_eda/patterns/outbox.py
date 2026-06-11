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
        # TODO: wrap the event into an OutboxMessage and append it to self._messages
        raise NotImplementedError

    def pending(self) -> list[OutboxMessage]:
        # TODO: return only messages where published is False
        raise NotImplementedError

    def mark_published(self, entry_id: str) -> None:
        for message in self._messages:
            if message.entry_id == entry_id:
                message.published = True
                return


class OutboxPublisher:
    def __init__(self, outbox: InMemoryOutbox, broker: RabbitMQTopicClient) -> None:
        self._outbox = outbox
        self._broker = broker

    def publish_pending(self) -> list[OutboxMessage]:
        # TODO: iterate over pending messages, publish each one via self._broker,
        # mark it published, and return the list of published messages
        raise NotImplementedError
