from __future__ import annotations


class InMemoryInbox:
    def __init__(self) -> None:
        self._processed_ids: set[str] = set()

    def has_processed(self, message_id: str) -> bool:
        # TODO: return True if message_id is already in the processed set
        raise NotImplementedError

    def mark_processed(self, message_id: str) -> None:
        # TODO: add message_id to the processed set
        raise NotImplementedError