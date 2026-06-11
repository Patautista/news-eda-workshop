from __future__ import annotations

from .config import AppSettings
from .patterns.inbox import InMemoryInbox
from .services.consumer import TopicNewsConsumer
from .services.messaging import RabbitMQTopicClient
from .utils.parsing import build_consumer_parser


def main() -> None:
    args = build_consumer_parser().parse_args()

    # Entry point wires dependencies only; TopicNewsConsumer owns runtime behavior.
    settings = AppSettings()
    broker = RabbitMQTopicClient(settings.rabbitmq)

    # TODO: create an InMemoryInbox
    # TODO: create a TopicNewsConsumer, injecting name, topic_patterns, broker, and inbox

    try:
        # TODO: start the consumer
        pass
    finally:
        broker.close()


if __name__ == "__main__":
    main()
