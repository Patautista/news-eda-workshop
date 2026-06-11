from __future__ import annotations

import random
import time

from .config import AppSettings
from .patterns.outbox import InMemoryOutbox, OutboxPublisher
from .services.gemini_client import GeminiNewsGenerator
from .services.messaging import BrokerUnavailableError, RabbitMQTopicClient
from .services.producer import FantasyNewsProducer
from .utils.parsing import build_producer_parser
from .topics import KNOWN_TOPICS


DEFAULT_TOPICS = KNOWN_TOPICS


def maybe_drop_message(*, drop_chance: float, event: object, index: int, interval: float) -> bool:
    # Simulate producer-side loss: event stays in outbox for later recovery.
    if random.random() < drop_chance:
        print(
            "Queued in outbox without publish attempt: "
            f"seq={index} topic={event.topic} id={event.id} title={event.title}"
        )
        time.sleep(interval)
        return True
    return False


def maybe_send_duplicate(*, duplicate_chance: float, event: object) -> set[str]:
    # Simulate at-least-once delivery by optionally republishing same message id.
    publish_duplicates: set[str] = set()
    if random.random() < duplicate_chance:
        publish_duplicates.add(event.id)
    return publish_duplicates


def main() -> None:
    args = build_producer_parser().parse_args()
    # If no topics are provided, cycle through the full known topic set.
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

            if maybe_drop_message(
                drop_chance=args.drop_chance,
                event=event,
                index=index,
                interval=args.interval,
            ):
                continue

            publish_duplicates = maybe_send_duplicate(
                duplicate_chance=args.duplicate_chance,
                event=event,
            )

            try:
                published_messages = publisher.publish_pending(duplicate_message_ids=publish_duplicates)
            except BrokerUnavailableError as error:
                print(
                    "RabbitMQ publish failed; keeping event in outbox for retry: "
                    f"topic={event.topic} id={event.id} error={error}"
                )
                time.sleep(args.interval)
                continue

            for message in published_messages:
                print(f"Published from outbox: seq={index} topic={message.topic} id={message.id}")
                if message.id in publish_duplicates:
                    print(f"Published duplicate from outbox: seq={index} topic={message.topic} id={message.id}")

            time.sleep(args.interval)
            index += 1

    except KeyboardInterrupt:
        # Flush pending outbox messages before shutdown to reduce event loss.
        print("Stopping producer. Flushing pending outbox messages...")
        remaining_messages = publisher.publish_pending()
        for message in remaining_messages:
            print(f"Recovered pending outbox message: topic={message.topic} id={message.id}")
    finally:
        broker.close()


if __name__ == "__main__":
    main()
