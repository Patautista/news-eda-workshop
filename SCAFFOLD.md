# Workshop Scaffold Branch

Participants implement the missing pieces. `main` is the reference solution.

Infrastructure, config, and RabbitMQ/Gemini adapters are given as-is. The files below require implementation.

---

## Files to implement

| File | What is missing |
|---|---|
| `services/producer.py` | The call that adds the created event to the outbox before returning |
| `services/consumer.py` | The inbox duplicate check in `_on_message`, mark-processed sequencing, and explicit failure-injection TODO checkpoints |
| `main_consumer.py` | Instantiation of `InMemoryInbox` and `TopicNewsConsumer`, and calling `consumer.start()` |
| `main_producer.py` | Instantiation of `InMemoryOutbox`, `FantasyNewsProducer`, and `OutboxPublisher`; the event creation and publish loop; flush on shutdown |
| `patterns/inbox.py` | `has_processed` and `mark_processed` method bodies |
| `patterns/outbox.py` | `add_event`, `pending`, `mark_published`, and `publish_pending` method bodies |

---

## Recommended order

1. `services/consumer.py` — implement handler flow and failure checkpoints
2. `services/producer.py` — keep producer focused on event creation
3. `main_consumer.py` — wire dependencies and start the runtime
4. `main_producer.py` — implement the basic publish loop first, then insert failure points to motivate outbox/inbox patterns
5. `patterns/inbox.py` — finalize dedup state behavior
6. `patterns/outbox.py` — finalize pending/published lifecycle and publishing orchestration

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
