from __future__ import annotations

from typing import Callable

import pika

from ..config import RabbitMQSettings


class RabbitMQTopicClient:
    def __init__(self, settings: RabbitMQSettings) -> None:
        credentials = pika.PlainCredentials(settings.user, settings.password)
        params = pika.ConnectionParameters(
            host=settings.host,
            port=settings.port,
            virtual_host=settings.vhost,
            credentials=credentials,
            heartbeat=60,
        )
        self._exchange = settings.exchange
        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()
        self._channel.exchange_declare(
            exchange=self._exchange,
            exchange_type="topic",
            durable=True,
        )

    def publish(self, routing_key: str, message: str) -> None:
        self._channel.basic_publish(
            exchange=self._exchange,
            routing_key=routing_key,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )

    def consume(
        self,
        queue_name: str,
        topic_patterns: list[str],
        callback: Callable,
        prefetch_count: int = 1,
    ) -> None:
        self._channel.queue_declare(queue=queue_name, durable=True)
        for pattern in topic_patterns:
            self._channel.queue_bind(
                exchange=self._exchange,
                queue=queue_name,
                routing_key=pattern,
            )

        self._channel.basic_qos(prefetch_count=prefetch_count)
        self._channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=False,
        )
        self._channel.start_consuming()

    def close(self) -> None:
        if self._connection.is_open:
            self._connection.close()
