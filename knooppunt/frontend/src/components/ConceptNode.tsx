import { Handle, Position, type NodeProps } from '@xyflow/react'
import type { NodeStatus } from '../types'

export interface ConceptNodeData {
  title: string
  status: NodeStatus
  selected: boolean
  diameter: number
}

const STATUS_CLASSES: Record<NodeStatus, string> = {
  completed:
    'bg-emerald-950/85 border-2 border-emerald-400 text-emerald-100 shadow-[0_0_20px_rgba(16,185,129,0.22)]',
  available:
    'bg-slate-900 border-2 border-indigo-400 text-slate-100 hover:border-indigo-300 shadow-[0_0_16px_rgba(99,102,241,0.18)]',
  locked:
    'bg-slate-900/60 border-2 border-slate-700 text-slate-400 hover:border-slate-500',
}

export default function ConceptNode({ data }: NodeProps) {
  const { title, status, selected, diameter } = data as unknown as ConceptNodeData
  const size = diameter || 140

  const selectionRing = selected
    ? status === 'completed'
      ? 'ring-4 ring-emerald-400/60 scale-105 shadow-[0_0_28px_rgba(16,185,129,0.45)]'
      : 'ring-4 ring-indigo-400/60 scale-105 shadow-[0_0_28px_rgba(99,102,241,0.45)]'
    : ''

  return (
    <div
      style={{ width: size, height: size }}
      className={`flex items-center justify-center rounded-full text-center p-4 transition-all duration-200 cursor-pointer select-none ${
        STATUS_CLASSES[status] ?? STATUS_CLASSES.locked
      } ${selectionRing}`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border-slate-800 !bg-slate-600"
      />
      <span
        className={`break-words font-semibold leading-snug line-clamp-3 ${
          size < 130 ? 'text-xs' : 'text-sm'
        }`}
      >
        {title}
      </span>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-slate-800 !bg-slate-600"
      />
    </div>
  )
}
