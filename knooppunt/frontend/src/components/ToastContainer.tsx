import {
  Award,
  GitBranch,
  GitMerge,
  Sparkles,
  Trophy,
  X,
  type LucideIcon,
} from 'lucide-react'
import type { ToastMessage } from '../types'

const TOAST_ICONS: Record<string, LucideIcon> = {
  Award,
  GitMerge,
  GitBranch,
  Sparkles,
  Trophy,
}

interface ToastContainerProps {
  toasts: ToastMessage[]
  onDismiss: (id: number) => void
}

export default function ToastContainer({
  toasts,
  onDismiss,
}: ToastContainerProps) {
  if (toasts.length === 0) return null

  return (
    <div className="pointer-events-none fixed right-4 top-4 z-50 flex w-[320px] max-w-[calc(100vw-2rem)] flex-col gap-2">
      {toasts.map((toast) => {
        const Icon = TOAST_ICONS[toast.icon] ?? Award
        return (
          <div
            key={toast.id}
            className="pointer-events-auto flex animate-[toast-in_0.2s_ease-out] items-start gap-3 rounded-xl border border-emerald-500/40 bg-slate-900 p-3.5 text-slate-100 shadow-2xl"
          >
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-emerald-500/15 text-emerald-300">
              <Icon size={17} />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-[12px] font-semibold text-slate-100">
                {toast.title}
              </p>
              <p className="mt-0.5 text-[11px] leading-relaxed text-slate-400">
                {toast.description}
              </p>
            </div>
            <button
              type="button"
              onClick={() => onDismiss(toast.id)}
              title="Melding sluiten"
              className="rounded p-0.5 text-slate-500 transition hover:bg-slate-800 hover:text-slate-300"
            >
              <X size={13} />
            </button>
          </div>
        )
      })}
    </div>
  )
}
