import { useEffect, useState } from 'react'
import {
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Info,
  Loader2,
  PlayCircle,
  RotateCcw,
  X,
  XCircle,
} from 'lucide-react'
import type { AnswerInput, NodeDetail, SubmitResult } from '../types'

interface NodeDrawerProps {
  node: NodeDetail | null
  loading: boolean
  submitting: boolean
  result: SubmitResult | null
  onClose: () => void
  onSelectNode: (nodeId: number) => void
  onSubmit: (answers: AnswerInput[]) => void
  onRetry: () => void
}

export default function NodeDrawer({
  node,
  loading,
  submitting,
  result,
  onClose,
  onSelectNode,
  onSubmit,
  onRetry,
}: NodeDrawerProps) {
  const [tab, setTab] = useState<'core' | 'quiz'>('core')
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<number, string>>({})

  useEffect(() => {
    setTab('core')
    setCurrentIndex(0)
    setAnswers({})
  }, [node?.id])

  useEffect(() => {
    if (result === null) {
      setCurrentIndex(0)
      setAnswers({})
    }
  }, [result])

  return (
    <div className="flex h-full w-[440px] max-w-full animate-[drawer-in_0.2s_ease-out] flex-col border-l border-slate-800 bg-slate-900 text-slate-100 shadow-2xl">
      <div className="flex items-start justify-between gap-3 border-b border-slate-800 px-5 py-4">
        <h2 className="min-w-0 text-base font-semibold leading-snug text-slate-100">
          {node ? node.title : 'Knoop laden…'}
        </h2>
        <button
          type="button"
          onClick={onClose}
          title="Sluiten"
          className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-slate-400 transition hover:bg-slate-800 hover:text-slate-200"
        >
          <X size={18} />
        </button>
      </div>

      {loading && !node ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 text-slate-400">
          <Loader2 size={22} className="animate-spin text-indigo-400" />
          <p className="text-xs">Knoop en 80/20-check laden…</p>
        </div>
      ) : !node ? (
        <div className="flex flex-1 items-center justify-center px-6 text-center text-xs text-slate-500">
          Deze knoop kon niet geladen worden.
        </div>
      ) : (
        <>
          {node.status === 'locked' && (
            <div className="mx-5 mt-4 flex items-start gap-2 rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2.5 text-[11px] leading-relaxed text-slate-400">
              <Info size={14} className="mt-0.5 shrink-0 text-slate-500" />
              <span>
                Tip: rond eerst de voorgaande knopen af voor het beste begrip.
              </span>
            </div>
          )}

          <div className="mt-4 flex gap-1 border-b border-slate-800 px-5">
            <button
              type="button"
              onClick={() => setTab('core')}
              className={`-mb-px border-b-2 px-2 pb-2.5 text-[12px] font-semibold transition ${
                tab === 'core'
                  ? 'border-indigo-400 text-indigo-300'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Kern &amp; Verbanden
            </button>
            <button
              type="button"
              onClick={() => setTab('quiz')}
              className={`-mb-px border-b-2 px-2 pb-2.5 text-[12px] font-semibold transition ${
                tab === 'quiz'
                  ? 'border-indigo-400 text-indigo-300'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              De 80/20 Check
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-5 py-5 scrollbar-thin">
            {tab === 'core' ? (
              <div>
                <p className="text-[13px] leading-relaxed text-slate-300">
                  {node.summary}
                </p>

                <p className="mt-5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                  Kernpunten
                </p>
                <ol className="mt-2 space-y-2.5">
                  {node.key_points.map((point, index) => (
                    <li
                      key={`${node.id}-point-${index}`}
                      className="flex gap-2.5 text-[13px] leading-relaxed text-slate-200"
                    >
                      <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-indigo-500/20 text-[10px] font-bold text-indigo-300">
                        {index + 1}
                      </span>
                      <span>{point}</span>
                    </li>
                  ))}
                </ol>

                {node.prerequisites.length > 0 && (
                  <div className="mt-5">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                      Hangt samen met
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {node.prerequisites.map((prerequisite) => (
                        <button
                          key={prerequisite.id}
                          type="button"
                          onClick={() => onSelectNode(prerequisite.id)}
                          className="inline-flex items-center gap-1.5 rounded-full border border-slate-700 bg-slate-800 px-2.5 py-1 text-[11px] font-medium text-slate-200 transition hover:bg-slate-700 hover:text-white"
                        >
                          <span
                            className={`h-1.5 w-1.5 rounded-full ${
                              prerequisite.status === 'completed'
                                ? 'bg-emerald-400'
                                : 'bg-amber-400'
                            }`}
                          />
                          {prerequisite.title}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  type="button"
                  onClick={() => setTab('quiz')}
                  disabled={node.quiz.length === 0}
                  className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <PlayCircle size={17} />
                  Start 80/20 Check
                </button>
              </div>
            ) : result ? (
              <ResultView
                node={node}
                result={result}
                onClose={onClose}
                onRetry={onRetry}
              />
            ) : (
              <QuizView
                node={node}
                answers={answers}
                currentIndex={currentIndex}
                submitting={submitting}
                setCurrentIndex={setCurrentIndex}
                setAnswers={setAnswers}
                onSubmit={onSubmit}
              />
            )}
          </div>
        </>
      )}
    </div>
  )
}

interface QuizViewProps {
  node: NodeDetail
  answers: Record<number, string>
  currentIndex: number
  submitting: boolean
  setCurrentIndex: (updater: (index: number) => number) => void
  setAnswers: (
    updater: (current: Record<number, string>) => Record<number, string>,
  ) => void
  onSubmit: (answers: AnswerInput[]) => void
}

function QuizView({
  node,
  answers,
  currentIndex,
  submitting,
  setCurrentIndex,
  setAnswers,
  onSubmit,
}: QuizViewProps) {
  const quiz = node.quiz
  if (quiz.length === 0) {
    return (
      <p className="text-xs text-slate-500">
        Voor deze knoop zijn nog geen vragen beschikbaar.
      </p>
    )
  }

  const safeIndex = Math.min(currentIndex, quiz.length - 1)
  const question = quiz[safeIndex]
  const answeredCount = quiz.filter(
    (item) => (answers[item.id] ?? '').trim().length > 0,
  ).length
  const allAnswered = answeredCount === quiz.length
  const isLast = safeIndex === quiz.length - 1

  const submit = () => {
    onSubmit(
      quiz.map((item) => ({
        question_id: item.id,
        answer: answers[item.id] ?? '',
      })),
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between text-[11px] font-medium text-slate-400">
        <span>
          Vraag {safeIndex + 1}/{quiz.length}
        </span>
        <span>
          {answeredCount}/{quiz.length} beantwoord
        </span>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className="h-full rounded-full bg-indigo-500 transition-all duration-300"
          style={{ width: `${((safeIndex + 1) / quiz.length) * 100}%` }}
        />
      </div>

      <div className="mt-4">
        {question.category === 'core_80' ? (
          <span className="inline-flex items-center rounded-full border border-indigo-500/30 bg-indigo-500/20 px-2 py-1 text-[10px] font-semibold text-indigo-300">
            Kernvraag (80%)
          </span>
        ) : (
          <span className="inline-flex items-center rounded-full border border-amber-500/30 bg-amber-500/20 px-2 py-1 text-[10px] font-semibold text-amber-300">
            Terugkoppeling naar: {question.linked_node_title ?? 'vorige knoop'}{' '}
            (20%)
          </span>
        )}

        <h3 className="mt-3 text-[15px] font-semibold leading-snug text-slate-100">
          {question.prompt}
        </h3>

        {question.question_type === 'short_open' ? (
          <textarea
            rows={4}
            value={answers[question.id] ?? ''}
            onChange={(event) =>
              setAnswers((current) => ({
                ...current,
                [question.id]: event.target.value,
              }))
            }
            placeholder="Typ je antwoord…"
            className="mt-4 w-full resize-none rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-[13px] leading-relaxed text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20"
          />
        ) : (
          <div className="mt-4 space-y-2">
            {question.options.map((option) => {
              const selected = answers[question.id] === option
              return (
                <button
                  key={option}
                  type="button"
                  onClick={() =>
                    setAnswers((current) => ({
                      ...current,
                      [question.id]: option,
                    }))
                  }
                  className={`flex w-full items-start gap-2.5 rounded-xl border px-3.5 py-3 text-left text-[13px] leading-snug transition ${
                    selected
                      ? 'border-indigo-400 bg-indigo-500/20 text-slate-100 ring-1 ring-indigo-400'
                      : 'border-slate-700 bg-slate-800/70 text-slate-100 hover:border-indigo-400'
                  }`}
                >
                  <span
                    className={`mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-full border ${
                      selected
                        ? 'border-indigo-400 bg-indigo-500 text-white'
                        : 'border-slate-500 bg-transparent'
                    }`}
                  >
                    {selected && <Check size={10} strokeWidth={3} />}
                  </span>
                  <span>{option}</span>
                </button>
              )
            })}
          </div>
        )}
      </div>

      <div className="mt-6 flex items-center justify-between gap-3">
        <button
          type="button"
          disabled={safeIndex === 0}
          onClick={() => setCurrentIndex((index) => Math.max(0, index - 1))}
          className="inline-flex items-center gap-1 rounded-lg border border-slate-700 px-3 py-2 text-[12px] font-medium text-slate-300 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ChevronLeft size={14} />
          Vorige
        </button>

        {!isLast ? (
          <button
            type="button"
            onClick={() =>
              setCurrentIndex((index) => Math.min(quiz.length - 1, index + 1))
            }
            className="inline-flex items-center gap-1 rounded-lg bg-indigo-600 px-3.5 py-2 text-[12px] font-semibold text-white transition hover:bg-indigo-500"
          >
            Volgende
            <ChevronRight size={14} />
          </button>
        ) : (
          <button
            type="button"
            disabled={!allAnswered || submitting}
            onClick={submit}
            className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-[12px] font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <CheckCircle2 size={14} />
            )}
            Controleer antwoorden
          </button>
        )}
      </div>

      {isLast && !allAnswered && (
        <p className="mt-2 text-center text-[10px] text-slate-500">
          Beantwoord alle vragen om te kunnen controleren.
        </p>
      )}
    </div>
  )
}

interface ResultViewProps {
  node: NodeDetail
  result: SubmitResult
  onClose: () => void
  onRetry: () => void
}

function ResultView({ node, result, onClose, onRetry }: ResultViewProps) {
  const correct = result.results.filter((item) => item.is_correct).length
  const total = result.results.length

  return (
    <div>
      <div className="text-center">
        <div
          className={`mx-auto grid h-20 w-20 place-items-center rounded-full ${
            result.passed
              ? 'bg-emerald-500/15 text-emerald-300'
              : 'bg-amber-500/15 text-amber-300'
          }`}
        >
          <span className="text-2xl font-bold">
            {Math.round(result.score_percentage)}%
          </span>
        </div>
        <p className="mt-3 text-sm font-semibold text-slate-100">
          {correct} van {total} juist
        </p>
        <p
          className={`mt-1 text-[12px] ${
            result.passed ? 'text-emerald-300' : 'text-slate-400'
          }`}
        >
          {result.passed
            ? 'Deze knoop is nu groen gekleurd.'
            : 'Je hebt 80% nodig om deze knoop af te ronden.'}
        </p>
      </div>

      <div className="mt-6 space-y-3">
        {node.quiz.map((question, index) => {
          const questionResult = result.results.find(
            (item) => item.question_id === question.id,
          )
          if (!questionResult) return null
          const isCorrect = questionResult.is_correct
          return (
            <div
              key={question.id}
              className={`rounded-xl border px-3.5 py-3 ${
                isCorrect
                  ? 'border-emerald-500/40 bg-emerald-950/60 text-emerald-200'
                  : 'border-rose-500/40 bg-rose-950/60 text-rose-200'
              }`}
            >
              <div className="flex items-start gap-2">
                {isCorrect ? (
                  <CheckCircle2
                    size={15}
                    className="mt-0.5 shrink-0 text-emerald-400"
                  />
                ) : (
                  <XCircle
                    size={15}
                    className="mt-0.5 shrink-0 text-rose-400"
                  />
                )}
                <div className="min-w-0">
                  <p className="text-[12px] font-semibold leading-snug text-slate-100">
                    {index + 1}. {question.prompt}
                  </p>
                  {!isCorrect && (
                    <p className="mt-1 text-[11px] leading-snug text-rose-300">
                      Juist antwoord:{' '}
                      <span className="font-medium">
                        {questionResult.correct_answer}
                      </span>
                    </p>
                  )}
                  <p
                    className={`mt-1 text-[11px] leading-relaxed ${
                      isCorrect ? 'text-emerald-200/80' : 'text-rose-200/80'
                    }`}
                  >
                    {questionResult.explanation}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="mt-6 flex flex-col gap-2">
        <button
          type="button"
          onClick={onClose}
          className="w-full rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500"
        >
          Terug naar de graaf
        </button>
        {!result.passed && (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex w-full items-center justify-center gap-1.5 rounded-xl border border-slate-700 px-4 py-2.5 text-sm font-semibold text-slate-300 transition hover:bg-slate-800"
          >
            <RotateCcw size={14} />
            Opnieuw proberen
          </button>
        )}
      </div>
    </div>
  )
}
