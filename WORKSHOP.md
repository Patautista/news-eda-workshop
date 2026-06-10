# Fantasy News Messaging Workshop

## Goal

This workshop is intentionally practical. The objective is not to explain EDA from first principles, but to help participants:

- navigate a small messaging-based Python codebase,
- understand how the project is structured,
- identify where messaging concerns should live,
- implement two important reliability patterns: outbox and inbox,
- use this repo as a sandbox for iterative improvement.

Time estimate: 2 to 3 hours.

---

## Outcomes

By the end of the workshop, participants should be able to:

- explain the role of each layer in this repo,
- run RabbitMQ, a producer, and one or more consumers,
- trace a message from creation to consumption,
- refactor the producer flow to use an in-memory outbox,
- refactor the consumer flow to use an in-memory inbox,
- identify what would need to change to make those patterns production-ready.

---

## Setup

### Prerequisites

- Python 3.10+
- Docker Desktop or Docker Engine
- A terminal

### Install dependencies

```bash
python -m pip install -e .
```

### Configure environment

PowerShell:

```powershell
Copy-Item .env.example .env
```

Bash:

```bash
cp .env.example .env
```

Optional: set `GEMINI_API_KEY` in `.env`. If left unset, the app uses fallback mock news generation.

### Start the stack

If you want only RabbitMQ:

PowerShell:

```powershell
.\scripts\start-rabbitmq.ps1
```

Bash:

```bash
bash ./scripts/start-rabbitmq.sh
```

If you want the full containerized demo:

```bash
docker compose up --build
```

RabbitMQ UI:

- http://localhost:15672
- user: `guest`
- password: `guest`

---

## Part 1: Use The Repo As-Is

Start here. The repo already gives you a working producer/consumer example, which is the right baseline before changing structure or patterns.

### Run one consumer

```bash
python -m news_eda.main_consumer --name sports-feed --topic arena.sports
```

### Run one producer

```bash
python -m news_eda.main_producer --topic arena.sports --count 3 --interval 1.0
```

### What participants should observe

- the producer CLI is thin and orchestration-focused,
- the consumer CLI is also thin and mostly wires dependencies,
- RabbitMQ details are isolated behind a messaging service,
- business payloads are represented as models,
- transport and application concerns are separated reasonably well for a workshop-sized project.

This is the first important lesson: a useful EDA project structure is mostly about separation of responsibilities, not about adding many abstractions.

---

## Part 2: Read The Structure, Not Just The Code

The most important practical skill in an EDA codebase is identifying where behavior belongs.

### Current structure

```text
src/news_eda/
├── services/
│   ├── gemini_client.py
│   ├── messaging.py
│   ├── producer.py
│   └── consumer.py
├── config.py
├── models.py
├── topics.py
├── main_producer.py
└── main_consumer.py
```

### How to interpret it

- `main_producer.py` and `main_consumer.py`
  Entry points only. These should parse arguments, build dependencies, and start the flow.

- `models.py`
  Message contracts and serialization. This is where the event shape lives.

- `services/producer.py`
  Application-side producer orchestration. It decides how a message is created and when it is published.

- `services/consumer.py`
  Application-side consumption flow. It decides what happens when a message arrives.

- `services/messaging.py`
  Infrastructure adapter around RabbitMQ. This should stay focused on broker interaction, not business rules.

- `services/gemini_client.py`
  External integration adapter. It produces content, but it should not know how messages are routed.

- `topics.py`
  Shared routing constraints. Good place for stable workshop-safe topic lists.

### Practical review exercise

Ask participants to trace one message through these files in this order:

1. `main_producer.py`
2. `services/producer.py`
3. `models.py`
4. `services/messaging.py`
5. `main_consumer.py`
6. `services/consumer.py`

The question to keep asking is: "Should this concern live here, or in a different layer?"

---

## Part 3: Recommended Structure For A Larger EDA Project

This repo is intentionally small, but for workshop purposes it helps to show the next logical step.

```text
src/news_eda/
├── application/
│   ├── commands/
│   ├── handlers/
│   └── services/
├── domain/
│   ├── events.py
│   ├── entities.py
│   └── value_objects.py
├── infrastructure/
│   ├── ai/
│   ├── messaging/
│   └── persistence/
├── patterns/
│   ├── outbox.py
│   └── inbox.py
├── config.py
└── entrypoints/
    ├── producer_cli.py
    └── consumer_cli.py
```

You do not need to implement all of this today. The point is to teach participants how to think about the boundaries:

- domain: what happened,
- application: what the system should do,
- infrastructure: how it talks to external systems,
- patterns: reliability and delivery guarantees,
- entrypoints: user-facing startup glue.

---

## Part 4: Outbox Pattern, Implemented In-Memory

This is the first best-practice pattern to implement during the workshop.

### Why it matters

The producer currently generates a news event and immediately publishes it. That is fine for a demo, but in a real system the business action and the publish step can drift apart.

The outbox pattern changes the flow:

1. create the business event,
2. write it to an outbox,
3. publish from the outbox,
4. mark it as published.

For this workshop, in-memory storage is enough because the goal is to learn the responsibilities and control flow.

### Suggested workshop file

Add a new module such as:

```text
src/news_eda/patterns/outbox.py
```

### Example implementation

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OutboxMessage:
    id: str
    topic: str
    payload: str
    published: bool = False


class InMemoryOutbox:
    def __init__(self) -> None:
        self._messages: list[OutboxMessage] = []

    def add(self, message: OutboxMessage) -> None:
        self._messages.append(message)

    def pending(self) -> list[OutboxMessage]:
        return [message for message in self._messages if not message.published]

    def mark_published(self, message_id: str) -> None:
        for message in self._messages:
            if message.id == message_id:
                message.published = True
                return
```

### Refactoring target

Refactor the producer flow conceptually into two steps:

1. `FantasyNewsProducer` creates `NewsEvent` and stores it in the outbox.
2. `OutboxPublisher` reads pending messages and publishes them through `RabbitMQTopicClient`.

### Suggested shape

```python
class FantasyNewsProducer:
    def __init__(self, generator, outbox) -> None:
        self._generator = generator
        self._outbox = outbox

    def create_news_event(self, topic: str) -> NewsEvent:
        article = self._generator.generate(topic)
        event = NewsEvent.create(
            topic=topic,
            title=article["title"],
            body=article["body"],
            source=article["source"],
        )
        self._outbox.add(
            OutboxMessage(
                id=event.id,
                topic=event.topic,
                payload=event.to_json(),
            )
        )
        return event


class OutboxPublisher:
    def __init__(self, outbox, broker) -> None:
        self._outbox = outbox
        self._broker = broker

    def publish_pending(self) -> None:
        for message in self._outbox.pending():
            self._broker.publish(routing_key=message.topic, message=message.payload)
            self._outbox.mark_published(message.id)
```

### Practical lesson

Participants should see that the outbox is not a broker concern. It is an application reliability concern that sits between business event creation and transport delivery.

### Exercise

1. Create `patterns/outbox.py`.
2. Move direct publish behavior out of `FantasyNewsProducer`.
3. Add a small publisher component that flushes pending outbox messages.
4. Update `main_producer.py` to create an outbox and publish pending messages after each event or at the end of the run.
5. Discuss how an in-memory outbox would become a DB-backed outbox in production.

---

## Part 5: Inbox Pattern, Implemented In-Memory

Now focus on the consumer side.

### Why it matters

Consumers should assume duplicate delivery is possible. The inbox pattern gives the consumer a place to record processed message IDs and skip work that already happened.

For the workshop, use an in-memory inbox to make the flow visible without introducing a database.

### Suggested workshop file

```text
src/news_eda/patterns/inbox.py
```

### Example implementation

```python
from __future__ import annotations


class InMemoryInbox:
    def __init__(self) -> None:
        self._processed_ids: set[str] = set()

    def has_processed(self, message_id: str) -> bool:
        return message_id in self._processed_ids

    def mark_processed(self, message_id: str) -> None:
        self._processed_ids.add(message_id)
```

### Refactoring target

Update the consumer flow so it:

1. deserializes the message,
2. checks whether the event ID is already in the inbox,
3. skips duplicate work if already processed,
4. otherwise handles the event and marks it as processed,
5. acknowledges the broker message.

### Suggested shape

```python
class TopicNewsConsumer:
    def __init__(self, name, topic_patterns, broker, inbox) -> None:
        self._name = name
        self._topic_patterns = topic_patterns
        self._broker = broker
        self._inbox = inbox
        self._queue_name = f"news.{name}.queue"

    def _on_message(self, ch, method, _properties, body: bytes) -> None:
        event = NewsEvent.from_json(body)

        if self._inbox.has_processed(event.id):
            print(f"[{self._name}] duplicate skipped: {event.id}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        print(f"[{self._name}] processing: {event.title}")
        self._inbox.mark_processed(event.id)
        ch.basic_ack(delivery_tag=method.delivery_tag)
```

### Practical lesson

The inbox belongs with consumer-side application behavior. It is not RabbitMQ state, and it is not part of the event model itself.

### Exercise

1. Create `patterns/inbox.py`.
2. Inject an inbox into the consumer.
3. Guard processing with `has_processed(event.id)`.
4. Add a temporary duplicate test by publishing the same serialized message twice.
5. Observe that only one copy is processed.

---

## Part 6: Workshop Flow

This sequence works well for a practical session.

### Step 1: Run the existing app

- start RabbitMQ,
- run one consumer,
- run one producer,
- confirm end-to-end flow.

### Step 2: Map responsibilities

- identify entrypoint files,
- identify service files,
- identify model and config files,
- discuss what belongs in each.

### Step 3: Implement outbox in memory

- add the outbox module,
- refactor producer service,
- add outbox flush behavior,
- rerun producer and consumer.

### Step 4: Implement inbox in memory

- add the inbox module,
- refactor consumer service,
- simulate duplicate delivery,
- verify deduplication behavior.

### Step 5: Review tradeoffs

- what works well in memory,
- what fails after process restart,
- what would need persistence,
- where retries, dead-lettering, and observability would fit next.

---

## Part 7: Suggested Facilitator Script

Use this as the actual workshop speaking track.

### Opening

"We are not going to spend time defining EDA terms. This repo already gives us a small messaging system. Our job is to inspect its structure, decide whether responsibilities are in the right places, and then improve reliability with inbox and outbox patterns."

### Repo walkthrough prompt

"Start at the CLI entrypoints. Do not start with RabbitMQ details. Find where the application flow begins, where the event is created, where the publish happens, and where consumption is handled."

### Producer refactor prompt

"Right now the producer creates and publishes in one flow. That is convenient, but it couples event creation to delivery. We are going to separate those responsibilities by introducing an outbox."

### Consumer refactor prompt

"Now assume duplicate delivery is normal. The consumer should be able to protect itself without depending on the broker to do that for us. That is where the inbox fits."

### Review prompt

"If this were production, which pieces would need durable storage first: event payloads, inbox state, or both? What failures become possible if they stay in memory?"

---

## Part 8: Best Practices To Emphasize

- keep entrypoints thin,
- keep broker code behind an adapter,
- keep event models explicit and serializable,
- do not mix transport details into business generation logic,
- treat duplicate delivery as expected,
- treat publication as a separate concern from event creation,
- add patterns for reliability before adding more features.

---

## Part 9: Optional Extensions

If the group moves quickly, use one of these:

1. Add a dead-letter flow for malformed messages.
2. Add a retry counter to the inbox or outbox records.
3. Persist the outbox to a local SQLite file.
4. Persist the inbox to a local SQLite file.
5. Split current `services/` into `application/` and `infrastructure/` packages.
6. Add tests around duplicate handling and pending-message publishing.

---

## Part 10: How To Get The Most From This Repo

- do not treat it as a finished architecture; treat it as a refactoring lab,
- make one reliability improvement at a time,
- rerun the producer and consumer after every change,
- keep comparing business flow versus transport flow,
- prefer small structural refactors over large rewrites,
- use the current code as a baseline, then layer patterns on top.

The most useful workshop result is not a bigger codebase. It is a clearer one.