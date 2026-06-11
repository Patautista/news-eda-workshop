import { useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

function ServiceNode({ data }) {
  return (
    <div className={`node node-${data.kind}`}>
      <Handle type="target" position={Position.Left} />
      <div className="node-title">{data.title}</div>
      {data.subtitle ? <div className="node-subtitle">{data.subtitle}</div> : null}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

const nodeTypes = { serviceNode: ServiceNode };

export default function App() {
  const [topology, setTopology] = useState({
    producers: [],
    rabbitmq: null,
    consumers: [],
  });
  const [error, setError] = useState("");
  const [showRawNames, setShowRawNames] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function refresh() {
      try {
        const response = await fetch("/api/topology");
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }
        const payload = await response.json();
        if (!cancelled) {
          setTopology(payload);
          setError("");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      }
    }

    refresh();
    const timer = setInterval(refresh, 4000);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  const { nodes, edges } = useMemo(() => {
    const producers = topology.producers || [];
    const consumers = topology.consumers || [];
    const rabbitmq = topology.rabbitmq;

    const getNodeTitle = (entity) => {
      if (showRawNames) {
        return entity.name;
      }
      return entity.displayName || entity.name;
    };

    const producerGap = 130;
    const consumerGap = 130;
    const producerStart = -((producers.length - 1) * producerGap) / 2;
    const consumerStart = -((consumers.length - 1) * consumerGap) / 2;

    const nextNodes = [];
    const nextEdges = [];

    producers.forEach((producer, index) => {
      const nodeId = `producer-${index}`;
      nextNodes.push({
        id: nodeId,
        type: "serviceNode",
        position: { x: 80, y: 330 + producerStart + index * producerGap },
        data: {
          kind: "producer",
          title: getNodeTitle(producer),
          subtitle: "Producer",
        },
      });

      if (rabbitmq) {
        nextEdges.push({
          id: `${nodeId}-to-rabbitmq`,
          source: nodeId,
          target: "rabbitmq",
          animated: true,
        });
      }
    });

    if (rabbitmq) {
      nextNodes.push({
        id: "rabbitmq",
        type: "serviceNode",
        position: { x: 530, y: 330 },
        data: {
          kind: "rabbitmq",
          title: getNodeTitle(rabbitmq),
          subtitle: "RabbitMQ Topic Exchange",
        },
      });
    }

    consumers.forEach((consumer, index) => {
      const nodeId = `consumer-${index}`;
      const topicSubtitle =
        consumer.topics && consumer.topics.length
          ? `Topics: ${consumer.topics.join(", ")}`
          : "Topics: unavailable";

      nextNodes.push({
        id: nodeId,
        type: "serviceNode",
        position: { x: 980, y: 330 + consumerStart + index * consumerGap },
        data: {
          kind: "consumer",
          title: getNodeTitle(consumer),
          subtitle: topicSubtitle,
        },
      });

      if (rabbitmq) {
        nextEdges.push({
          id: `rabbitmq-to-${nodeId}`,
          source: "rabbitmq",
          target: nodeId,
          animated: true,
        });
      }
    });

    return { nodes: nextNodes, edges: nextEdges };
  }, [topology, showRawNames]);

  return (
    <div className="app-shell">
      <header className="header">
        <div className="header-main">
          <h1>Runtime Architecture</h1>
          <label className="toggle-raw-names">
            <input
              type="checkbox"
              checked={showRawNames}
              onChange={(event) => setShowRawNames(event.target.checked)}
            />
            Show raw container names
          </label>
        </div>
        <p>
          {error
            ? `Error loading topology: ${error}`
            : "Live container graph. Use mouse wheel or controls to zoom."}
        </p>
      </header>

      <main className="flow-wrapper">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.35}
          maxZoom={2.25}
          proOptions={{ hideAttribution: true }}
        >
          <MiniMap pannable zoomable />
          <Controls showInteractive />
          <Background gap={20} size={1} />
        </ReactFlow>
      </main>
    </div>
  );
}
