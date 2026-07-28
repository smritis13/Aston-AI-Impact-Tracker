import React, { useMemo } from 'react';

import 'reactflow/dist/style.css';
import '@reactflow/controls/dist/style.css';
import { Background } from 'reactflow';
import ReactFlow, { Controls } from 'reactflow';

interface WorkflowGraphProps {
  graphDefinition: {
    nodes: any[];
    edges: any[];
  };
}

const nodeTypes = {
  start: { style: { background: '#4CAF50', color: 'white' } },
  process: { style: { background: '#2196F3', color: 'white' } },
  end: { style: { background: '#F44336', color: 'white' } },
};

const WorkflowGraph: React.FC<WorkflowGraphProps> = ({ graphDefinition }) => {
  const nodes: any[] = useMemo(
    () =>
      graphDefinition.nodes.map((node) => ({
        id: node.id,
        type: 'default',
        data: { 
          label: node.data.label,
        },
        position: { x: 0, y: 0 }, // Initial position
        style: {
          ...nodeTypes[node.type as keyof typeof nodeTypes]?.style,
          padding: 10,
          borderRadius: 5,
        },
      })),
    [graphDefinition.nodes]
  );

  const edges: any[] = useMemo(
    () =>
      graphDefinition.edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: 'smoothstep',
        animated: true,
      })),
    [graphDefinition.edges]
  );

  // Auto-layout the nodes in a top-down manner
  React.useEffect(() => {
    const layoutNodes = () => {
      const levelMap = new Map<string, number>();
      const visited = new Set<string>();

      const findLevel = (nodeId: string, level: number) => {
        if (visited.has(nodeId)) return;
        visited.add(nodeId);
        levelMap.set(nodeId, Math.max(level, levelMap.get(nodeId) || 0));

        const outgoingEdges = graphDefinition.edges.filter(
          (edge) => edge.source === nodeId
        );
        outgoingEdges.forEach((edge) => {
          findLevel(edge.target, level + 1);
        });
      };

      // Find start nodes (nodes with no incoming edges)
      const startNodes = graphDefinition.nodes.filter(
        (node) =>
          !graphDefinition.edges.some((edge) => edge.target === node.id)
      );

      startNodes.forEach((node) => findLevel(node.id, 0));

      // Position nodes based on their levels
      nodes.forEach((node) => {
        const level = levelMap.get(node.id) || 0;
        const nodesAtLevel = Array.from(levelMap.entries()).filter(
          ([, l]) => l === level
        ).length;
        const index = Array.from(levelMap.entries())
          .filter(([, l]) => l === level)
          .findIndex(([id]) => id === node.id);

        node.position = {
          x: (index - (nodesAtLevel - 1) / 2) * 200,
          y: level * 100,
        };
      });
    };

    layoutNodes();
  }, [graphDefinition.edges, graphDefinition.nodes, nodes]);

  return (
    <div style={{ width: '100%', height: '500px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        attributionPosition="bottom-left"
      >
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
};

export default WorkflowGraph; 