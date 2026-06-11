from __future__ import annotations

import argparse

from .config import AppSettings
from .patterns.inbox import InMemoryInbox
from .services.consumer import TopicNewsConsumer
from .services.messaging import RabbitMQTopicClient
from .topics import KNOWN_TOPICS


def parse_topics_csv(value: str) -> list[str]:
    topics = [topic.strip() for topic in value.split(",") if topic.strip()]
    if not topics:
        raise argparse.ArgumentTypeError("Provide at least one topic.")

    invalid_topics = [topic for topic in topics if topic not in KNOWN_TOPICS]
    if invalid_topics:
        known_topics_display = ", ".join(KNOWN_TOPICS)
        invalid_display = ", ".join(invalid_topics)
        raise argparse.ArgumentTypeError(
            f"Unknown topic(s): {invalid_display}. Known topics: {known_topics_display}."
        )

    return topics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Subscribe to fantasy news topics.")
    parser.add_argument("--name", required=True, help="Consumer instance name.")
    parser.add_argument(
        "--topics",
        type=parse_topics_csv,
        required=True,
        help="Comma-separated known topics to subscribe to.",
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
