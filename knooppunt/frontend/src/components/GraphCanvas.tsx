import { useCallback, useEffect } from 'react'
import {
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  Panel,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
  type NodeMouseHandler,
} from '@xyflow/react'
import { Zap } from 'lucide-react'
import ConceptNode, { type ConceptNodeData } from './ConceptNode'
import { layoutGraph } from '../utils/layout'
import type { CourseGraph, Metrics } from '../types'

const nodeTypes = { concept: ConceptNode }

interface GraphCanvasProps {
  graph: CourseGraph
  metrics: Metrics | null
  selectedNodeId: number | null
  onNodeSelect: (nodeId: number) => void
}

function formatTokens(value: number): string {
  if (value >= 1000) {
    const short = value / 1000
    return `${Number.isInteger(short) ? short.toFixed(0) : short.toFixed(1)}k`
  }
  return String(value)
}

function LegendRow({ color, label }: { color: string; label: string }) {
  return (
    <li className="flex items-center gap-2">
      <span className={`h-2 w-2 rounded-full ${color}`} />
      {label}
    </li>
  )
}

export default function GraphCanvas({
  graph,
  metrics,
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
        color: '#94a3b8',
      },
      style: { stroke: '#cbd5e1', strokeWidth: 1.6 },
      label: edge.relation_label,
      labelShowBg: true,
      labelBgStyle: { fill: '#ffffff', stroke: '#e2e8f0' },
      labelBgPadding: [6, 2],
      labelBgBorderRadius: 6,
      labelStyle: { fontSize: 10, fill: '#64748b' },
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
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-6 py-4">
        <div className="min-w-0">
          <h1 className="truncate text-lg font-semibold tracking-tight text-slate-900">
            {graph.course.title}
          </h1>
          <p className="mt-0.5 text-xs text-slate-500">
            Voortgang: {graph.course.completed_nodes}/{graph.course.total_nodes}{' '}
            knopen ({progress}%)
          </p>
        </div>

        {metrics && (
          <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-[11px] font-medium text-slate-600">
            <Zap size={13} className="shrink-0 text-amber-500" />
            <span className="whitespace-nowrap">
              AI-calls: {metrics.layer1_calls} Graaf |{' '}
              {metrics.layer3_calls} Redenering | Zonder AI:{' '}
              {metrics.zero_ai_actions} | Bespaard: ~
              {formatTokens(metrics.tokens_saved_est)} tokens
            </span>
          </div>
        )}
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
          className="bg-slate-50"
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={22}
            size={1.4}
            color="#cbd5e1"
          />
          <Controls
            position="bottom-left"
            showInteractive={false}
            className="!rounded-lg !border !border-slate-200 !bg-white !shadow-sm"
          />
          <Panel position="bottom-right">
            <div className="rounded-xl border border-slate-200 bg-white/95 px-3 py-2 shadow-sm backdrop-blur">
              <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                Legende
              </p>
              <ul className="space-y-1.5 text-[11px] text-slate-600">
                <LegendRow color="bg-emerald-500" label="Voltooid" />
                <LegendRow color="bg-indigo-500" label="Beschikbaar" />
                <LegendRow color="bg-slate-300" label="Nog niet bereikt" />
              </ul>
            </div>
          </Panel>
        </ReactFlow>
      </div>
    </div>
  )
}
