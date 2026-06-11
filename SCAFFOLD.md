# Workshop Scaffold Branch

Participants implement the missing pieces. `main` is the reference solution.

Infrastructure, config, and RabbitMQ/Gemini adapters are given as-is. The files below require implementation.

---

## Files to implement

| File | What is missing |
|---|---|
| `patterns/inbox.py` | `has_processed` and `mark_processed` method bodies |
| `patterns/outbox.py` | `add_event`, `pending`, `mark_published`, and `publish_pending` method bodies |
| `services/producer.py` | The call that adds the created event to the outbox before returning |
| `services/consumer.py` | The inbox duplicate check in `_on_message`, and marking the event processed after handling |
| `main_consumer.py` | Instantiation of `InMemoryInbox` and `TopicNewsConsumer`, and calling `consumer.start()` |
| `main_producer.py` | Instantiation of `InMemoryOutbox`, `FantasyNewsProducer`, and `OutboxPublisher`; the event creation and publish loop; flush on shutdown |

---

## Recommended order

1. `patterns/inbox.py` — simplest; establish the deduplication concept
2. `patterns/outbox.py` — three cooperating pieces; understand why publisher is separate from storage
3. `services/producer.py` — one insertion; confirm the producer has no knowledge of the broker
4. `services/consumer.py` — two insertions in `_on_message`; order matters
5. `main_consumer.py` — wiring only
6. `main_producer.py` — wiring plus error handling and flush-on-shutdown

---

## Verification

```bash
# Terminal 1
python -m news_eda.main_consumer --name all-news --topics "arena.sports,arena.fantasy,arena.transfers"

# Terminal 2
python -m news_eda.main_producer
```

---

## Bonus extensions

1. **Simulate drops** — add `--drop-chance`; skip `publish_pending` probabilistically; observe the event stays in the outbox
2. **Simulate duplicates** — add `--duplicate-chance`; republish the same message ID; verify the inbox deduplicates it
3. **SQLite outbox** — replace the in-memory list with a SQLite-backed store behind the same interface
4. **SQLite inbox** — replace the in-memory set with SQLite; verify it survives process restarts
5. **Dead-letter path** — catch malformed messages in `_on_message` and route them to a `dead_letter` key instead of acking
