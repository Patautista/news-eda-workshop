import express from "express";
import path from "node:path";
import Docker from "dockerode";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const distDir = path.resolve(__dirname, "../dist");

const app = express();
const docker = new Docker({ socketPath: "/var/run/docker.sock" });

function sanitizeContainerName(container) {
  return container.Names?.[0]?.replace(/^\//, "") || container.Id.slice(0, 12);
}

function getComposeProject(container) {
  return container.Labels?.["com.docker.compose.project"] || "";
}

function getContainerNumber(container) {
  const value = container.Labels?.["com.docker.compose.container-number"];
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function toDisplayName(container) {
  const service = getServiceName(container);
  const number = getContainerNumber(container);
  if (service) {
    return number && number > 1 ? `${service}-${number}` : service;
  }

  const raw = sanitizeContainerName(container);
  const project = getComposeProject(container);
  let cleaned = raw;

  if (project && cleaned.startsWith(`${project}-`)) {
    cleaned = cleaned.slice(project.length + 1);
  }

  return cleaned.replace(/-\d+$/, "");
}

function parseTopics(command) {
  if (!command) {
    return [];
  }

  const topics = [];
  const tokens = command.match(/(?:[^\s"]+|"[^"]*")+/g) || [];

  const normalize = (token) => token.replace(/^"|"$/g, "");
  const addMany = (value) => {
    value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
      .forEach((item) => topics.push(item));
  };

  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];

    if (token === "--topic" && tokens[index + 1]) {
      topics.push(normalize(tokens[index + 1]));
      index += 1;
      continue;
    }

    if (token === "--topics" && tokens[index + 1]) {
      addMany(normalize(tokens[index + 1]));
      index += 1;
      continue;
    }

    if (token.startsWith("--topics=")) {
      addMany(normalize(token.slice("--topics=".length)));
      continue;
    }

    if (token.startsWith("--topic=")) {
      topics.push(normalize(token.slice("--topic=".length)));
    }
  }

  return [...new Set(topics)];
}

function getServiceName(container) {
  return container.Labels?.["com.docker.compose.service"] || "";
}

function isRabbitMqContainer(container) {
  const service = getServiceName(container);
  const image = container.Image || "";
  return service === "rabbitmq" || image.includes("rabbitmq");
}

function isProducerContainer(container) {
  const service = getServiceName(container);
  const command = container.Command || "";
  return service.startsWith("producer") || command.includes("news_eda.main_producer");
}

function isConsumerContainer(container) {
  const service = getServiceName(container);
  const command = container.Command || "";
  return service.startsWith("consumer") || command.includes("news_eda.main_consumer");
}

app.get("/api/topology", async (_req, res) => {
  try {
    const containers = await docker.listContainers({ all: false });

    const producers = containers.filter(isProducerContainer).map((container) => ({
      name: sanitizeContainerName(container),
      displayName: toDisplayName(container),
    }));

    const rabbitContainer = containers.find(isRabbitMqContainer) || null;
    const rabbitmq = rabbitContainer
      ? {
          name: sanitizeContainerName(rabbitContainer),
          displayName: toDisplayName(rabbitContainer),
        }
      : null;

    const consumers = containers.filter(isConsumerContainer).map((container) => ({
      name: sanitizeContainerName(container),
      displayName: toDisplayName(container),
      topics: parseTopics(container.Command),
    }));

    res.json({
      producers,
      rabbitmq,
      consumers,
    });
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : String(error),
    });
  }
});

app.use(express.static(distDir));
app.get("*", (_req, res) => {
  res.sendFile(path.join(distDir, "index.html"));
});

const port = Number(process.env.PORT || 8080);
app.listen(port, () => {
  console.log(`Topology UI listening on port ${port}`);
});
