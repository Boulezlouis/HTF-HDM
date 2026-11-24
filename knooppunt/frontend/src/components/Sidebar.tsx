import { useState } from 'react'
import {
  Award,
  Check,
  GitBranch,
  GitMerge,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Sparkles,
  Trash2,
  Trophy,
  X,
  type LucideIcon,
} from 'lucide-react'
import type { Achievement, CourseSummary } from '../types'

const ACHIEVEMENT_ICONS: Record<string, LucideIcon> = {
  Award,
  GitMerge,
  GitBranch,
  Sparkles,
  Trophy,
}

interface SidebarProps {
  open: boolean
  onToggle: () => void
  courses: CourseSummary[]
  activeCourseId: number | null
  achievements: Achievement[]
  onSelectCourse: (courseId: number) => void
  onCreateCourse: () => void
  onDeleteCourse: (courseId: number) => void
  onShowAchievements: () => void
}

export default function Sidebar({
  open,
  onToggle,
  courses,
  activeCourseId,
  achievements,
  onSelectCourse,
  onCreateCourse,
  onDeleteCourse,
  onShowAchievements,
}: SidebarProps) {
  const [confirmingId, setConfirmingId] = useState<number | null>(null)

  const unlocked = achievements
    .filter((achievement) => achievement.unlocked_at !== null)
    .sort(
      (a, b) =>
        new Date(b.unlocked_at as string).getTime() -
        new Date(a.unlocked_at as string).getTime(),
    )
  const recent = unlocked.slice(0, 2)
  const totalAchievements = achievements.length || 5

  if (!open) {
    return (
      <aside className="flex w-14 shrink-0 flex-col items-center gap-3 border-r border-slate-800 bg-slate-900 py-4 transition-all duration-200">
        <button
          type="button"
          onClick={onToggle}
          title="Zijbalk uitklappen"
          className="grid h-8 w-8 place-items-center rounded-lg text-slate-400 transition hover:bg-slate-800 hover:text-slate-100"
        >
          <PanelLeftOpen size={17} />
        </button>
        <div className="grid h-8 w-8 place-items-center rounded-lg bg-indigo-600 text-sm font-bold text-white">
          K
        </div>
      </aside>
    )
  }

  return (
    <aside className="flex w-[260px] shrink-0 flex-col border-r border-slate-800 bg-slate-900 text-slate-100 transition-all duration-200">
      <div className="flex items-center justify-between px-4 pb-3 pt-4">
        <div className="flex min-w-0 items-center gap-2">
          <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-indigo-600 text-sm font-bold text-white">
            K
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold leading-none text-slate-100">
              KnoopPunt
            </p>
            <p className="mt-1 truncate text-[10px] text-slate-400">
              Leer met verbanden
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={onToggle}
          title="Zijbalk inklappen"
          className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-slate-400 transition hover:bg-slate-800 hover:text-slate-200"
        >
          <PanelLeftClose size={17} />
        </button>
      </div>

      <button
        type="button"
        onClick={onCreateCourse}
        className="mx-4 mb-5 flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 active:scale-[0.99]"
      >
        <Plus size={16} strokeWidth={2.5} />
        Nieuw vak aanmaken
      </button>

      <div className="flex-1 overflow-y-auto px-2 pb-3 scrollbar-thin">
        <p className="px-2 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Mijn vakken
        </p>

        {courses.length === 0 && (
          <p className="px-2 py-3 text-[11px] leading-relaxed text-slate-500">
            Nog geen vakken. Maak je eerste vak aan met een PDF of PPTX.
          </p>
        )}

        <div className="space-y-0.5">
          {courses.map((course) => {
            const active = course.id === activeCourseId
            const percentage = Math.max(
              0,
              Math.min(100, Math.round(course.progress_percentage)),
            )
            return (
              <div
                key={course.id}
                className={`group flex items-center rounded-lg border transition ${
                  active
                    ? 'border-indigo-500/40 bg-indigo-500/15 text-white'
                    : 'border-transparent hover:bg-slate-800/80'
                }`}
              >
                <button
                  type="button"
                  onClick={() => onSelectCourse(course.id)}
                  className="min-w-0 flex-1 px-3 py-2.5 text-left"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`truncate text-[13px] font-medium ${
                        active ? 'text-white' : 'text-slate-300'
                      }`}
                    >
                      {course.title}
                    </span>
                    <span className="shrink-0 text-[11px] font-semibold text-slate-400">
                      {percentage}%
                    </span>
                  </div>
                  <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-slate-800">
                    <div
                      className="h-full rounded-full bg-emerald-500 transition-all duration-300"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </button>

                <div className="flex shrink-0 items-center pr-1">
                  {confirmingId === course.id ? (
                    <div className="flex items-center gap-0.5">
                      <button
                        type="button"
                        title="Bevestig verwijderen"
                        onClick={() => {
                          setConfirmingId(null)
                          onDeleteCourse(course.id)
                        }}
                        className="rounded p-1 text-rose-400 transition hover:bg-rose-500/10"
                      >
                        <Check size={13} />
                      </button>
                      <button
                        type="button"
                        title="Annuleer"
                        onClick={() => setConfirmingId(null)}
                        className="rounded p-1 text-slate-500 transition hover:bg-slate-800"
                      >
                        <X size={13} />
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      title="Vak verwijderen"
                      onClick={() => setConfirmingId(course.id)}
                      className="rounded p-1 text-slate-600 opacity-0 transition hover:bg-rose-500/10 hover:text-rose-400 focus:opacity-100 group-hover:opacity-100"
                    >
                      <Trash2 size={13} />
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="border-t border-slate-800 px-3 py-3">
        <p className="px-1 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Mijn achievements
        </p>

        {recent.length === 0 ? (
          <p className="px-1 py-1 text-[11px] text-slate-500">
            Nog geen achievements
          </p>
        ) : (
          <div className="space-y-1.5">
            {recent.map((achievement) => {
              const Icon = ACHIEVEMENT_ICONS[achievement.icon] ?? Award
              return (
                <div
                  key={achievement.code}
                  className="flex items-start gap-2 rounded-lg bg-slate-800/60 px-2 py-1.5"
                >
                  <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-indigo-500/20 text-indigo-300">
                    <Icon size={14} />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-[11px] font-semibold text-slate-200">
                      {achievement.title}
                    </p>
                    <p className="line-clamp-2 text-[10px] leading-snug text-slate-400">
                      {achievement.description}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        <button
          type="button"
          onClick={onShowAchievements}
          className="mt-2 w-full rounded-lg border border-slate-700 px-2 py-1.5 text-[11px] font-medium text-slate-300 transition hover:bg-slate-800"
        >
          Bekijk alle ({unlocked.length}/{totalAchievements})
        </button>
      </div>
    </aside>
  )
}
