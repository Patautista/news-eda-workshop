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


def chance(value: str) -> float:
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("Chance values must be between 0 and 1.")
    return parsed


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
    parser.add_argument(
        "--duplicate-chance",
        type=chance,
        default=0.25,
        help="Chance that a published event is intentionally published twice.",
    )
    parser.add_argument(
        "--drop-chance",
        type=chance,
        default=0.2,
        help="Chance that an intended event is generated but intentionally not published.",
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
        for index in range(1, args.count + 1):
            topic = random.choice(topics)
            event = producer.create_event(topic)

            if random.random() < args.drop_chance:
                print(
                    "Dropped intended publish: "
                    f"seq={index} topic={event.topic} id={event.id} title={event.title}"
                )
                time.sleep(args.interval)
                continue

            producer.publish_event(event)
            print(f"Published: seq={index} topic={event.topic} id={event.id} title={event.title}")

            if random.random() < args.duplicate_chance:
                producer.publish_event(event)
                print(
                    "Published duplicate: "
                    f"seq={index} topic={event.topic} id={event.id} title={event.title}"
                )

            time.sleep(args.interval)
    finally:
        broker.close()


if __name__ == "__main__":
    main()
