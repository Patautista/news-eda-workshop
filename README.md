# Fantasy News EDA Workshop

A basic event-driven architecture (EDA) system in Python that:

- generates mock/fantasy news (optionally using Gemini),
- publishes news events to RabbitMQ topic exchange,
- lets consumers subscribe to different topic patterns via queues.

## Architecture

- `Producer` generates news and publishes to topic exchange `fantasy.news.topic`.
- `RabbitMQ` routes by routing keys like `arena.sports` or `kingdom.politics`.
- `Consumers` bind their own queue to one or more known predefined topics.

Known topics:

- `kingdom.politics`
- `arena.sports`
- `guild.economy`
- `wilds.weather`
- `arcane.science`

## Project Structure

```text
.
|- src/news_eda/
|  |- config.py
|  |- gemini_client.py
|  |- messaging.py
|  |- models.py
|  |- producer.py
|  |- consumer.py
|  |- main_producer.py
|  \- main_consumer.py
|- scripts/
|  |- start-rabbitmq.ps1
|  \- start-rabbitmq.sh
|- docker-compose.yml
|- .env.example
|- pyproject.toml
\- requirements.txt
```

## Prerequisites

- Python 3.10+
- Docker Desktop (or Docker Engine)

## Setup

1. Copy env file:
   - PowerShell: `Copy-Item .env.example .env`
   - Bash: `cp .env.example .env`
2. Optional: set `GEMINI_API_KEY` in `.env` to use Gemini. If omitted, the app uses deterministic fallback mock text.
3. Install dependencies:
   - `python -m pip install -e .`

## Start RabbitMQ

- PowerShell: `./scripts/start-rabbitmq.ps1`
- Bash: `bash ./scripts/start-rabbitmq.sh`

RabbitMQ endpoints:

- AMQP: `localhost:5672`
- Management UI: `http://localhost:15672` (user/password: `guest`/`guest`)

## Run Consumers (topic subscriptions)

Open one terminal per consumer:

```bash
python -m news_eda.main_consumer --name politics-feed --topic kingdom.politics
python -m news_eda.main_consumer --name sports-feed --topic arena.sports
python -m news_eda.main_consumer --name mixed-feed --topic guild.economy --topic wilds.weather
```

## Run Producer

```bash
python -m news_eda.main_producer --count 10 --interval 1.0
```

Or constrain to specific topics:

```bash
python -m news_eda.main_producer --topic arena.sports --topic kingdom.politics --count 6
```

## Notes

- Both producer and consumer CLIs only accept the known topic list shown above.
- Messages are persisted (`delivery_mode=2`) and queues are durable.
