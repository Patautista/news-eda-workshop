from __future__ import annotations

import time
from typing import Callable

import pika
from pika.exceptions import AMQPError

from ..config import RabbitMQSettings


class BrokerUnavailableError(RuntimeError):
    pass


class RabbitMQTopicClient:
    def __init__(self, settings: RabbitMQSettings) -> None:
        self._settings = settings
        self._exchange = settings.exchange
        self._connection: pika.BlockingConnection | None = None
        self._channel = None

    def _connection_parameters(self) -> pika.ConnectionParameters:
        credentials = pika.PlainCredentials(self._settings.user, self._settings.password)
        return pika.ConnectionParameters(
            host=self._settings.host,
            port=self._settings.port,
            virtual_host=self._settings.vhost,
            credentials=credentials,
            heartbeat=60,
        )

    def _connect(self) -> None:
        self._connection = pika.BlockingConnection(self._connection_parameters())
        self._channel = self._connection.channel()
        self._channel.exchange_declare(
            exchange=self._exchange,
            exchange_type="topic",
            durable=True,
        )

    def _ensure_channel(self):
        if self._connection is None or self._channel is None or self._connection.is_closed:
            self._connect()
        return self._channel

    def _close_safely(self) -> None:
        if self._connection is not None and self._connection.is_open:
            self._connection.close()
        self._connection = None
        self._channel = None

    def _with_retry(self, operation: Callable[[], None]) -> None:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                operation()
                return
            except (AMQPError, OSError) as error:
                last_error = error
                self._close_safely()
                if attempt < 2:
                    time.sleep(0.5 * (attempt + 1))

        if last_error is not None:
            raise BrokerUnavailableError("RabbitMQ is unavailable after retries.") from last_error

    def publish(self, routing_key: str, message: str) -> None:
        def operation() -> None:
            channel = self._ensure_channel()
            channel.basic_publish(
                exchange=self._exchange,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2),
            )

        self._with_retry(operation)

    def consume(
        self,
        queue_name: str,
        topic_patterns: list[str],
        callback: Callable,
        prefetch_count: int = 1,
    ) -> None:
        channel = self._ensure_channel()
        channel.queue_declare(queue=queue_name, durable=True)
        for pattern in topic_patterns:
            channel.queue_bind(
                exchange=self._exchange,
                queue=queue_name,
                routing_key=pattern,
            )

        channel.basic_qos(prefetch_count=prefetch_count)
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=False,
        )
        channel.start_consuming()

    def close(self) -> None:
        self._close_safely()
