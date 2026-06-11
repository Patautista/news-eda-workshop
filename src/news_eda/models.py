from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True)
class NewsEvent:
    id: str
    topic: str
    title: str
    body: str
    source: str
    created_at: str

    @classmethod
    def create(cls, topic: str, title: str, body: str, source: str) -> "NewsEvent":
        now = datetime.now(tz=timezone.utc).isoformat()
        return cls(
            id=str(uuid4()),
            topic=topic,
            title=title,
            body=body,
            source=source,
            created_at=now,
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=True)

    @classmethod
    def from_json(cls, payload: bytes | str) -> "NewsEvent":
        if isinstance(payload, bytes):
            data = json.loads(payload.decode("utf-8"))
        else:
            data = json.loads(payload)
        return cls(**data)
