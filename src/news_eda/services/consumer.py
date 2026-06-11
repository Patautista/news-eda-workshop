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
        # TODO: artificial failure point A: raise before deserialize to simulate malformed transport payloads.
        event = NewsEvent.from_json(body)

        # TODO: check if this event has already been processed using self._inbox
        # If it has, print a skip message, ack the broker message, and return early.
        # TODO: artificial failure point B: raise after deserialize but before dedup to test retry/redelivery behavior.

        print(
            f"[{self._name}] {event.created_at} | topic={event.topic} | "
            f"title={event.title} | source={event.source}"
        )
        print(f"[{self._name}] {event.body}\n")

        # TODO: mark the event as processed in the inbox
        # TODO: artificial failure point C: raise after business handling but before mark_processed.
        # TODO: artificial failure point D: raise after mark_processed but before ack to test idempotent redelivery.
        ch.basic_ack(delivery_tag=method.delivery_tag)
