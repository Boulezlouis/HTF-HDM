import dagre from '@dagrejs/dagre'
import type { Edge, Node } from '@xyflow/react'

/**
 * Diameter van een knoop op basis van moeilijkheid en hoeveelheid leerstof.
 * Schaalt vloeiend van 110px (makkelijk/klein) tot 180px (moeilijk/groot).
 */
export function getNodeDiameter(
  difficulty = 3,
  contentVolume = 3,
): number {
  const weight = difficulty * 0.6 + contentVolume * 0.4
  return Math.round(110 + ((weight - 1) / 4) * 70)
}

function readDiameter(node: Node): number {
  const data = node.data as { diameter?: number } | undefined
  return data?.diameter ?? getNodeDiameter()
}

/**
 * Berekent een top-down (TB) Dagre-layout met per knoop een eigen diameter.
 */
export function layoutGraph(nodes: Node[], edges: Edge[]): Node[] {
  const graph = new dagre.graphlib.Graph()
  graph.setDefaultEdgeLabel(() => ({}))
  graph.setGraph({ rankdir: 'TB', nodesep: 70, ranksep: 100 })

  nodes.forEach((node) => {
    const diameter = readDiameter(node)
    graph.setNode(node.id, {
      width: diameter + 20,
      height: diameter + 20,
    })
  })
  edges.forEach((edge) => {
    graph.setEdge(edge.source, edge.target)
  })

  dagre.layout(graph)

  return nodes.map((node) => {
    const position = graph.node(node.id) as { x: number; y: number }
    const diameter = readDiameter(node)
    return {
      ...node,
      position: {
        x: position.x - diameter / 2,
        y: position.y - diameter / 2,
      },
    }
  })
}
