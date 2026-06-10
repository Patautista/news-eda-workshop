from __future__ import annotations

import argparse
import random
import time

from .config import AppSettings
from .services.gemini_client import GeminiNewsGenerator
from .services.messaging import RabbitMQTopicClient
from .services.producer import FantasyNewsProducer
from .topics import KNOWN_TOPICS


DEFAULT_TOPICS = KNOWN_TOPICS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish mock fantasy news events.")
    parser.add_argument(
        "--topic",
        action="append",
        dest="topics",
        choices=KNOWN_TOPICS,
        help="Routing key topic to publish to; can be repeated.",
    )
    parser.add_argument("--count", type=int, default=5, help="Number of events to publish.")
    parser.add_argument(
        "--interval",
        type=float,
        default=1.5,
        help="Seconds between messages.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    topics = args.topics or DEFAULT_TOPICS

    settings = AppSettings()
    broker = RabbitMQTopicClient(settings.rabbitmq)
    generator = GeminiNewsGenerator(settings.gemini)
    producer = FantasyNewsProducer(generator=generator, broker=broker)

    try:
        for _ in range(args.count):
            topic = random.choice(topics)
            event = producer.generate_and_publish(topic)
            print(f"Published: topic={event.topic} id={event.id} title={event.title}")
            time.sleep(args.interval)
    finally:
        broker.close()


if __name__ == "__main__":
    main()
