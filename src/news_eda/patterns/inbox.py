from __future__ import annotations


class InMemoryInbox:
    def __init__(self) -> None:
        self._processed_ids: set[str] = set()

    def has_processed(self, message_id: str) -> bool:
        return message_id in self._processed_ids

    def mark_processed(self, message_id: str) -> None:
        self._processed_ids.add(message_id)