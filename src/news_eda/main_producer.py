from __future__ import annotations

import random
import time

from .config import AppSettings
from .patterns.outbox import InMemoryOutbox, OutboxPublisher
from .services.faulty_client import FaultyRabbitClient
from .services.gemini_client import GeminiNewsGenerator
from .services.messaging import BrokerUnavailableError, RabbitMQTopicClient
from .services.producer import FantasyNewsProducer
from .utils.parsing import build_producer_parser
from .topics import get_concrete_topics


DEFAULT_TOPICS = get_concrete_topics()


def main() -> None:
    args = build_producer_parser().parse_args()
    # If no topics are provided, cycle through the full known topic set.
    topics = args.topics or DEFAULT_TOPICS

    settings = AppSettings()
    broker = RabbitMQTopicClient(settings.rabbitmq)
    faulty_broker = FaultyRabbitClient(
        broker,
        drop_chance=args.drop_chance,
        duplicate_chance=args.duplicate_chance,
    )
    generator = GeminiNewsGenerator(settings.gemini)
    outbox = InMemoryOutbox()
    producer = FantasyNewsProducer(generator=generator, outbox=outbox)
    publisher = OutboxPublisher(outbox=outbox, broker=faulty_broker)

    index = 1
    try:
        while True:
            topic = random.choice(topics)
            event = producer.create_event(topic)

            try:
                published_messages = publisher.publish_pending(index=index)
            except BrokerUnavailableError as error:
                print(
                    "RabbitMQ publish failed; keeping event in outbox for retry: "
                    f"topic={event.topic} id={event.id} error={error}"
                )
                time.sleep(args.interval)
                continue

            published_event_ids: set[str] = set()
            for message in published_messages:
                print(f"Published from outbox: seq={index} topic={message.topic} id={message.id}")
                if message.id in published_event_ids:
                    print(f"Published duplicate from outbox: seq={index} topic={message.topic} id={message.id}")
                published_event_ids.add(message.id)

            time.sleep(args.interval)
            index += 1

    except KeyboardInterrupt:
        # Flush pending outbox messages before shutdown to reduce event loss.
        print("Stopping producer. Flushing pending outbox messages...")
        remaining_messages = publisher.publish_pending(index=index, allow_faults=False)
        for message in remaining_messages:
            print(f"Recovered pending outbox message: topic={message.topic} id={message.id}")
    finally:
        broker.close()


if __name__ == "__main__":
    main()
