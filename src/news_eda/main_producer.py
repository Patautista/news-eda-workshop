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


def main() -> None:
    args = build_producer_parser().parse_args()
    # If no topics are provided, cycle through the full known topic set.
    topics = args.topics or DEFAULT_TOPICS

    settings = AppSettings()
    broker = RabbitMQTopicClient(settings.rabbitmq)
    generator = GeminiNewsGenerator(settings.gemini)

    # TODO: create an InMemoryOutbox
    # TODO: create a FantasyNewsProducer, injecting the generator and outbox
    # TODO: create an OutboxPublisher, injecting the outbox and broker

    index = 1
    try:
        while True:
            topic = random.choice(topics)

            # TODO: call producer.create_event(topic) and capture the event

            try:
                # TODO: call publisher.publish_pending() and capture published messages
                pass
            except BrokerUnavailableError as error:
                print(f"Publish failed, event stays in outbox: {error}")
                time.sleep(args.interval)
                continue

            # TODO: print each published message
            # Hint: use message.topic and message.id

            time.sleep(args.interval)
            index += 1

    except KeyboardInterrupt:
        print("Stopping producer. Flushing pending outbox messages...")
        # TODO: flush remaining outbox messages and print each one
    finally:
        broker.close()


if __name__ == "__main__":
    main()
