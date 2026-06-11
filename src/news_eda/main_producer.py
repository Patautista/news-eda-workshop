from __future__ import annotations

import argparse
import random
import time

from .config import AppSettings
from .patterns.outbox import InMemoryOutbox, OutboxPublisher
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
    outbox = InMemoryOutbox()
    producer = FantasyNewsProducer(generator=generator, outbox=outbox)
    publisher = OutboxPublisher(outbox=outbox, broker=broker)

    index = 1
    try:
        while True:
            topic = random.choice(topics)
            event = producer.create_event(topic)

            if random.random() < args.drop_chance:
                print(
                    "Queued in outbox without publish attempt: "
                    f"seq={index} topic={event.topic} id={event.id} title={event.title}"
                )
                time.sleep(args.interval)
                continue

            publish_duplicates = set()
            if random.random() < args.duplicate_chance:
                publish_duplicates.add(event.id)

            published_messages = publisher.publish_pending(duplicate_message_ids=publish_duplicates)
            for message in published_messages:
                print(f"Published from outbox: seq={index} topic={message.topic} id={message.id}")
                if message.id in publish_duplicates:
                    print(f"Published duplicate from outbox: seq={index} topic={message.topic} id={message.id}")

            time.sleep(args.interval)
            index += 1

    except KeyboardInterrupt:
        print("Stopping producer. Flushing pending outbox messages...")
        remaining_messages = publisher.publish_pending()
        for message in remaining_messages:
            print(f"Recovered pending outbox message: topic={message.topic} id={message.id}")
    finally:
        broker.close()


if __name__ == "__main__":
    main()
