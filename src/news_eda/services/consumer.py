from __future__ import annotations

from typing import Any

from ..patterns.inbox import InMemoryInbox
from .messaging import RabbitMQTopicClient
from ..models import NewsEvent


class TopicNewsConsumer:
    def __init__(
        self,
        name: str,
        topic_patterns: list[str],
        broker: RabbitMQTopicClient,
        inbox: InMemoryInbox,
    ) -> None:
        self._name = name
        self._topic_patterns = topic_patterns
        self._broker = broker
        self._inbox = inbox
        self._queue_name = f"news.{name}.queue"

    def start(self) -> None:
        print(
            f"[{self._name}] listening on queue={self._queue_name} "
            f"topics={','.join(self._topic_patterns)}"
        )
        self._broker.consume(
            queue_name=self._queue_name,
            topic_patterns=self._topic_patterns,
            callback=self._on_message,
        )

    def _on_message(self, ch: Any, method: Any, _properties: Any, body: bytes) -> None:
        event = NewsEvent.from_json(body)

        if self._inbox.has_processed(event.id):
            print(f"[{self._name}] duplicate skipped: topic={event.topic} id={event.id}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        print(
            f"[{self._name}] {event.created_at} | topic={event.topic} | "
            f"title={event.title} | source={event.source}"
        )
        print(f"[{self._name}] {event.body}\n")
        self._inbox.mark_processed(event.id)
        ch.basic_ack(delivery_tag=method.delivery_tag)
