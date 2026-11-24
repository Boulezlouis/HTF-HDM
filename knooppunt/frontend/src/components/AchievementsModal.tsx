import {
  Award,
  GitBranch,
  GitMerge,
  Sparkles,
  Trophy,
  X,
  type LucideIcon,
} from 'lucide-react'
import type { Achievement } from '../types'

const ACHIEVEMENT_ICONS: Record<string, LucideIcon> = {
  Award,
  GitMerge,
  GitBranch,
  Sparkles,
  Trophy,
}

interface AchievementsModalProps {
  open: boolean
  achievements: Achievement[]
  onClose: () => void
}

function formatDate(value: string | null): string {
  if (!value) return ''
  return new Date(value).toLocaleDateString('nl-NL', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

export default function AchievementsModal({
  open,
  achievements,
  onClose,
}: AchievementsModalProps) {
  if (!open) return null

  const unlockedCount = achievements.filter(
    (achievement) => achievement.unlocked_at !== null,
  ).length
  const total = achievements.length || 5

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <div className="flex max-h-[90vh] w-full max-w-md flex-col overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 text-slate-100 shadow-2xl">
        <div className="flex items-start justify-between gap-3 border-b border-slate-800 px-5 py-4">
          <div className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-amber-500/15 text-amber-300">
              <Trophy size={18} />
            </span>
            <div>
              <h2 className="text-base font-semibold text-slate-100">
                Achievements
              </h2>
              <p className="mt-0.5 text-[11px] text-slate-400">
                {unlockedCount} van {total} ontgrendeld
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            title="Sluiten"
            className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-slate-400 transition hover:bg-slate-800 hover:text-slate-200"
          >
            <X size={18} />
          </button>
        </div>

        <div className="overflow-y-auto px-4 py-4 scrollbar-thin">
          <ul className="space-y-2">
            {achievements.map((achievement) => {
              const unlocked = achievement.unlocked_at !== null
              const Icon = ACHIEVEMENT_ICONS[achievement.icon] ?? Award
              return (
                <li
                  key={achievement.code}
                  className={`flex items-start gap-3 rounded-xl border px-3.5 py-3 transition ${
                    unlocked
                      ? 'border-emerald-500/40 bg-emerald-950/40'
                      : 'border-slate-800 bg-slate-950/40'
                  }`}
                >
                  <span
                    className={`grid h-9 w-9 shrink-0 place-items-center rounded-full ${
                      unlocked
                        ? 'bg-emerald-500/15 text-emerald-300'
                        : 'bg-slate-800 text-slate-500'
                    }`}
                  >
                    <Icon size={17} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p
                        className={`truncate text-[13px] font-semibold ${
                          unlocked ? 'text-slate-100' : 'text-slate-400'
                        }`}
                      >
                        {achievement.title}
                      </p>
                      {unlocked ? (
                        <span className="shrink-0 rounded-full bg-emerald-500/15 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-emerald-300">
                          Behaald
                        </span>
                      ) : (
                        <span className="shrink-0 rounded-full bg-slate-800 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-slate-400">
                          Vergrendeld
                        </span>
                      )}
                    </div>
                    <p className="mt-0.5 text-[11px] leading-relaxed text-slate-400">
                      {achievement.description}
                    </p>
                    {unlocked && (
                      <p className="mt-1 text-[10px] text-emerald-300/70">
                        Behaald op {formatDate(achievement.unlocked_at)}
                      </p>
                    )}
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      </div>
    </div>
  )
}
