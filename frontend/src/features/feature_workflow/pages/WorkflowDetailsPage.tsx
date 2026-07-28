import React from 'react';
import { useParams } from 'react-router-dom';
import MainLayout from 'core/components/layout/MainLayout';
import Loading from 'core/components/Loading';
import Error from 'core/components/Error';
import TimeAgoWidget from 'core/components/shared/TimeAgoWidget';
import BreadcrumbWidget from 'core/components/shared/BreadcrumbWidget';
import useWorkflow from '../hooks/useWorkflow';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
} from 'reactflow';
import 'reactflow/dist/style.css';

const WorkflowDetailsPage: React.FC = () => {
  const { workflowId } = useParams<{ workflowId: string }>();
  const { data: workflow, isLoading, error } = useWorkflow(workflowId);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  React.useEffect(() => {
    if (workflow?.graph_definition) {
      // Transform nodes to ReactFlow format
      const flowNodes = workflow.graph_definition.nodes.map((node: any) => ({
        id: node.id,
        type: 'default',
        position: { x: 0, y: 0 }, // Initial position
        data: { 
          label: node.data.label,
        },
        style: {
          background: getNodeColor(node.type),
          color: 'white',
          padding: 10,
          borderRadius: 5,
          width: 150,
        },
      }));

      // Transform edges to ReactFlow format
      const flowEdges = workflow.graph_definition.edges.map((edge: any) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: 'smoothstep',
        animated: true,
      }));

      // Auto-layout nodes in a top-down manner
      const layoutNodes = () => {
        const levelMap = new Map<string, number>();
        const visited = new Set<string>();

        const findLevel = (nodeId: string, level: number) => {
          if (visited.has(nodeId)) return;
          visited.add(nodeId);
          levelMap.set(nodeId, Math.max(level, levelMap.get(nodeId) || 0));

          const outgoingEdges = workflow.graph_definition.edges.filter(
            (edge: any) => edge.source === nodeId
          );
          outgoingEdges.forEach((edge: any) => {
            findLevel(edge.target, level + 1);
          });
        };

        // Find start nodes
        const startNodes = workflow.graph_definition.nodes.filter(
          (node: any) =>
            !workflow.graph_definition.edges.some((edge: any) => edge.target === node.id)
        );

        startNodes.forEach((node: any) => findLevel(node.id, 0));

        // Position nodes
        return flowNodes.map((node: any) => {
          const level = levelMap.get(node.id) || 0;
          const nodesAtLevel = Array.from(levelMap.entries()).filter(
            ([, l]) => l === level
          ).length;
          const index = Array.from(levelMap.entries())
            .filter(([, l]) => l === level)
            .findIndex(([id]) => id === node.id);

          return {
            ...node,
            position: {
              x: (index - (nodesAtLevel - 1) / 2) * 200,
              y: level * 100,
            },
          };
        });
      };

      const layoutedNodes = layoutNodes();
      setNodes(layoutedNodes);
      setEdges(flowEdges);
    }
  }, [workflow, setNodes, setEdges]);

  const onConnect = React.useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  if (isLoading) return <Loading isLoading={isLoading} />;
  if (error) return <Error error={error + ""} />;
  if (!workflow) return <Error error="Workflow not found" />;

  return (
    <MainLayout>
      <div className="container-fluid">
        <BreadcrumbWidget
          mainTitle={workflow.name}
          breadcrumbs={[
            { title: "Dashboard", url: "/" },
            { title: "Workflows", url: "/workflows" },
            { title: workflow.name },
          ]}
        />

        <div className="row">
          <div className="col-xl-12">
            <div className="card custom-card">
              <div className="card-header">
                <h3 className="card-title">{workflow.name}</h3>
                <div className="text-muted">
                  Created <TimeAgoWidget date={workflow.created_at} />
                </div>
              </div>
              <div className="card-body">
                <div className="mb-4">
                  <h4>Description</h4>
                  <p>{workflow.description}</p>
                </div>

                <div className="mb-4">
                  <h4>Workflow Graph</h4>
                  <div style={{ width: '100%', height: '500px', border: '1px solid #ddd' }}>
                    <ReactFlow
                      nodes={nodes}
                      edges={edges}
                      onNodesChange={onNodesChange}
                      onEdgesChange={onEdgesChange}
                      onConnect={onConnect}
                      fitView
                    >
                      <MiniMap />
                      <Controls />
                      <Background />
                    </ReactFlow>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

// Helper function to get node colors based on type
const getNodeColor = (type: string): string => {
  switch (type) {
    case 'start':
      return '#4CAF50';
    case 'process':
      return '#2196F3';
    case 'end':
      return '#F44336';
    default:
      return '#607D8B';
  }
};

export default WorkflowDetailsPage;