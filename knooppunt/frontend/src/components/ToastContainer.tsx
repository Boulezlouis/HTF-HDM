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
            className="pointer-events-auto flex animate-[toast-in_0.2s_ease-out] items-start gap-3 rounded-xl border border-slate-200 bg-white/95 p-3.5 shadow-lg backdrop-blur"
          >
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-emerald-100 text-emerald-600">
              <Icon size={17} />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-[12px] font-semibold text-slate-800">
                {toast.title}
              </p>
              <p className="mt-0.5 text-[11px] leading-relaxed text-slate-500">
                {toast.description}
              </p>
            </div>
            <button
              type="button"
              onClick={() => onDismiss(toast.id)}
              title="Melding sluiten"
              className="rounded p-0.5 text-slate-300 transition hover:bg-slate-100 hover:text-slate-500"
            >
              <X size={13} />
            </button>
          </div>
        )
      })}
    </div>
  )
}
