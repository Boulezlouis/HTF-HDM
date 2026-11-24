import { CheckCircle2, CircleDot, Lock } from 'lucide-react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import type { NodeStatus } from '../types'

export interface ConceptNodeData {
  title: string
  status: NodeStatus
  selected: boolean
}

const STATUS_META: Record<
  NodeStatus,
  {
    card: string
    icon: string
    iconComponent: typeof CheckCircle2
    badge: string
    label: string
  }
> = {
  completed: {
    card: 'border-emerald-500 bg-emerald-50 text-emerald-950',
    icon: 'text-emerald-600',
    iconComponent: CheckCircle2,
    badge: 'bg-emerald-100 text-emerald-700',
    label: 'Voltooid',
  },
  available: {
    card: 'border-indigo-500 bg-white text-slate-800',
    icon: 'text-indigo-500',
    iconComponent: CircleDot,
    badge: 'bg-indigo-50 text-indigo-600',
    label: 'Beschikbaar',
  },
  locked: {
    card: 'border-slate-300 bg-slate-100 text-slate-400',
    icon: 'text-slate-400',
    iconComponent: Lock,
    badge: 'bg-slate-200 text-slate-500',
    label: 'Nog niet bereikt',
  },
}

export default function ConceptNode({ data }: NodeProps) {
  const { title, status, selected } = data as unknown as ConceptNodeData
  const meta = STATUS_META[status] ?? STATUS_META.locked
  const Icon = meta.iconComponent

  return (
    <div
      className={`relative w-[230px] min-h-[74px] rounded-xl border-2 px-3.5 py-3 text-left transition-all duration-200 ${
        meta.card
      } ${
        selected
          ? 'ring-4 ring-indigo-400/50 scale-[1.03] shadow-lg'
          : 'shadow-sm hover:shadow-md'
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border-0 !bg-slate-300"
      />
      <div className="flex items-start gap-2">
        <Icon size={16} strokeWidth={2.4} className={`mt-0.5 shrink-0 ${meta.icon}`} />
        <div className="min-w-0 flex-1">
          <p className="line-clamp-2 text-[13px] font-semibold leading-snug">
            {title}
          </p>
          <span
            className={`mt-1.5 inline-flex items-center rounded-full px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide ${meta.badge}`}
          >
            {meta.label}
          </span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-0 !bg-slate-300"
      />
    </div>
  )
}
