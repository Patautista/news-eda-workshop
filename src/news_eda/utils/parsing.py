from __future__ import annotations

import argparse

from ..topics import KNOWN_TOPICS


def chance(value: str) -> float:
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("Chance values must be between 0 and 1.")
    return parsed


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
