import { useCallback, useEffect } from 'react'
import {
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
  type NodeMouseHandler,
} from '@xyflow/react'
import ConceptNode, { type ConceptNodeData } from './ConceptNode'
import { getNodeDiameter, layoutGraph } from '../utils/layout'
import type { CourseGraph } from '../types'

const nodeTypes = { concept: ConceptNode }

interface GraphCanvasProps {
  graph: CourseGraph
  selectedNodeId: number | null
  onNodeSelect: (nodeId: number) => void
}

export default function GraphCanvas({
  graph,
  selectedNodeId,
  onNodeSelect,
}: GraphCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  useEffect(() => {
    const flowNodes: Node[] = graph.nodes.map((node) => ({
      id: String(node.id),
      type: 'concept',
      position: { x: 0, y: 0 },
      data: {
        title: node.title,
        status: node.status,
        selected: node.id === selectedNodeId,
        diameter: getNodeDiameter(node.difficulty, node.content_volume),
      } satisfies ConceptNodeData,
    }))

    const flowEdges: Edge[] = graph.edges.map((edge) => ({
      id: `edge-${edge.id}`,
      source: String(edge.source_node_id),
      target: String(edge.target_node_id),
      type: 'smoothstep',
      markerEnd: {
        type: MarkerType.ArrowClosed,
        width: 18,
        height: 18,
        color: '#64748b',
      },
      style: { stroke: '#475569', strokeWidth: 1.6 },
      label: edge.relation_label,
      labelShowBg: true,
      labelBgStyle: { fill: '#0f172a', stroke: '#334155' },
      labelBgPadding: [6, 2],
      labelBgBorderRadius: 6,
      labelStyle: { fontSize: 11, fill: '#cbd5e1' },
    }))

    setNodes(layoutGraph(flowNodes, flowEdges))
    setEdges(flowEdges)
    // selectedNodeId wordt in een aparte effect bijgewerkt; de layout hangt
    // enkel van de graaf af.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graph, setNodes, setEdges])

  useEffect(() => {
    setNodes((current) =>
      current.map((node) => ({
        ...node,
        data: {
          ...(node.data as unknown as ConceptNodeData),
          selected: Number(node.id) === selectedNodeId,
        },
      })),
    )
  }, [selectedNodeId, setNodes])

  const handleNodeClick = useCallback<NodeMouseHandler>(
    (_event, node) => {
      onNodeSelect(Number(node.id))
    },
    [onNodeSelect],
  )

  const progress = Math.round(graph.course.progress_percentage)

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-slate-800 bg-slate-900/90 px-6 py-4 text-slate-100">
        <h1 className="truncate text-lg font-semibold tracking-tight text-slate-100">
          {graph.course.title}
        </h1>
        <p className="mt-0.5 text-xs text-slate-400">
          Voortgang: {graph.course.completed_nodes}/{graph.course.total_nodes}{' '}
          knopen ({progress}%)
        </p>
      </header>

      <div className="relative flex-1">
        <ReactFlow
          key={graph.course.id}
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          onNodeClick={handleNodeClick}
          fitView
          fitViewOptions={{ padding: 0.25 }}
          minZoom={0.35}
          maxZoom={1.6}
          nodesConnectable={false}
          className="bg-slate-950"
        >
          <Background
            variant={BackgroundVariant.Dots}
            color="#1e293b"
            gap={22}
            size={1.5}
          />
          <Controls
            position="bottom-left"
            showInteractive={false}
            className="!rounded-lg"
          />
        </ReactFlow>
      </div>
    </div>
  )
}
