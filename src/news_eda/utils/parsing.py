from __future__ import annotations

import argparse

from ..topics import KNOWN_TOPICS


def build_producer_parser() -> argparse.ArgumentParser:
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
    return parser


def build_consumer_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Subscribe to fantasy news topics.")
    parser.add_argument("--name", required=True, help="Consumer instance name.")
    parser.add_argument(
        "--topics",
        type=parse_topics_csv,
        required=True,
        help="Comma-separated known topics to subscribe to.",
    )
    return parser


def parse_topics_csv(value: str) -> list[str]:
    # Accept a single CLI argument and expand it into a normalized topic list.
    topics = [topic.strip() for topic in value.split(",") if topic.strip()]
    if not topics:
        raise argparse.ArgumentTypeError("Provide at least one topic.")

    # Fail fast so invalid routing keys never reach broker bindings.
    invalid_topics = [topic for topic in topics if topic not in KNOWN_TOPICS]
    if invalid_topics:
        known_topics_display = ", ".join(KNOWN_TOPICS)
        invalid_display = ", ".join(invalid_topics)
        raise argparse.ArgumentTypeError(
            f"Unknown topic(s): {invalid_display}. Known topics: {known_topics_display}."
        )

    return topics
