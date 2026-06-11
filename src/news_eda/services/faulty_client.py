from __future__ import annotations

import random

from ..models import NewsEvent
from .messaging import RabbitMQTopicClient


class FaultyRabbitClient:
    def __init__(self, broker: RabbitMQTopicClient, *, drop_chance: float, duplicate_chance: float) -> None:
        self._broker = broker
        self._drop_chance = drop_chance
        self._duplicate_chance = duplicate_chance

    def publish(
        self,
        *,
        routing_key: str,
        message: str,
        index: int,
        allow_faults: bool = True,
    ) -> bool:
        event = NewsEvent.from_json(message)

        if allow_faults and random.random() < self._drop_chance:
            print(
                "Queued in outbox without publish attempt: "
                f"seq={index} topic={event.topic} id={event.id} title={event.title}"
            )
            return False

        self._broker.publish(routing_key=routing_key, message=message)

        if allow_faults and random.random() < self._duplicate_chance:
            print(
                "Published duplicate from outbox: "
                f"seq={index} topic={event.topic} id={event.id} title={event.title}"
            )
            self._broker.publish(routing_key=routing_key, message=message)

        return True