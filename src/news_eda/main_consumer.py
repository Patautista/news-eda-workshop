from __future__ import annotations

import argparse

from .config import AppSettings
from .patterns.inbox import InMemoryInbox
from .services.consumer import TopicNewsConsumer
from .services.messaging import RabbitMQTopicClient
from .topics import KNOWN_TOPICS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Subscribe to fantasy news topics.")
    parser.add_argument("--name", required=True, help="Consumer instance name.")
    parser.add_argument(
        "--topic",
        action="append",
        dest="topics",
        required=True,
        choices=KNOWN_TOPICS,
        help="Known topic to subscribe to. Repeatable.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    settings = AppSettings()
    broker = RabbitMQTopicClient(settings.rabbitmq)
    inbox = InMemoryInbox()
    consumer = TopicNewsConsumer(
        name=args.name,
        topic_patterns=args.topics,
        broker=broker,
        inbox=inbox,
    )

    try:
        consumer.start()
    finally:
        broker.close()


if __name__ == "__main__":
    main()
