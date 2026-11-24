import { useCallback, useEffect, useRef, useState } from 'react'
import { Layers, Loader2, Plus } from 'lucide-react'
import {
  deleteCourse,
  getAchievements,
  getCourseGraph,
  getCourses,
  getMetrics,
  getNode,
  submitQuiz,
} from './api'
import AchievementsModal from './components/AchievementsModal'
import CreateCourseModal from './components/CreateCourseModal'
import GraphCanvas from './components/GraphCanvas'
import NodeDrawer from './components/NodeDrawer'
import Sidebar from './components/Sidebar'
import ToastContainer from './components/ToastContainer'
import type {
  Achievement,
  AnswerInput,
  CourseGraph,
  CourseSummary,
  Metrics,
  NodeDetail,
  SubmitResult,
  ToastMessage,
} from './types'

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : 'Er ging iets mis. Probeer het opnieuw.'
}

export default function App() {
  const [courses, setCourses] = useState<CourseSummary[]>([])
  const [activeCourseId, setActiveCourseId] = useState<number | null>(null)
  const [graph, setGraph] = useState<CourseGraph | null>(null)
  const [graphLoading, setGraphLoading] = useState(false)
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [achievements, setAchievements] = useState<Achievement[]>([])

  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null)
  const [nodeDetail, setNodeDetail] = useState<NodeDetail | null>(null)
  const [nodeLoading, setNodeLoading] = useState(false)
  const [quizResult, setQuizResult] = useState<SubmitResult | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [achievementsOpen, setAchievementsOpen] = useState(false)
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const toastIdRef = useRef(1)

  const dismissToast = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const pushToast = useCallback(
    (title: string, description: string, icon = 'Award') => {
      const id = toastIdRef.current
      toastIdRef.current += 1
      setToasts((current) => [...current, { id, title, description, icon }])
      window.setTimeout(() => {
        setToasts((current) => current.filter((toast) => toast.id !== id))
      }, 5000)
    },
    [],
  )

  const selectCourse = useCallback(
    async (courseId: number) => {
      setActiveCourseId(courseId)
      setSelectedNodeId(null)
      setNodeDetail(null)
      setQuizResult(null)
      setGraphLoading(true)
      try {
        const data = await getCourseGraph(courseId)
        setGraph(data)
        setMetrics(await getMetrics())
      } catch (error) {
        setGraph(null)
        pushToast('Graaf laden mislukt', errorMessage(error), 'Sparkles')
      } finally {
        setGraphLoading(false)
      }
    },
    [pushToast],
  )

  useEffect(() => {
    let cancelled = false
    const boot = async () => {
      try {
        const [courseList, achievementList] = await Promise.all([
          getCourses(),
          getAchievements(),
        ])
        if (cancelled) return
        setAchievements(achievementList)
        setCourses(courseList)
        if (courseList.length > 0) {
          await selectCourse(courseList[0].id)
        } else {
          setMetrics(await getMetrics())
        }
      } catch (error) {
        if (!cancelled) {
          pushToast('Kon de app niet laden', errorMessage(error), 'Sparkles')
        }
      }
    }
    void boot()
    return () => {
      cancelled = true
    }
  }, [selectCourse, pushToast])

  const openNode = useCallback(
    async (nodeId: number) => {
      setSelectedNodeId(nodeId)
      setQuizResult(null)
      setNodeDetail(null)
      setNodeLoading(true)
      try {
        const detail = await getNode(nodeId)
        setNodeDetail(detail)
        setMetrics(await getMetrics())
      } catch (error) {
        setSelectedNodeId(null)
        pushToast('Knoop laden mislukt', errorMessage(error), 'Sparkles')
      } finally {
        setNodeLoading(false)
      }
    },
    [pushToast],
  )

  const closeDrawer = useCallback(() => {
    setSelectedNodeId(null)
    setNodeDetail(null)
    setQuizResult(null)
  }, [])

  const handleSubmit = useCallback(
    async (answers: AnswerInput[]) => {
      if (selectedNodeId === null) return
      setSubmitting(true)
      try {
        const result = await submitQuiz(selectedNodeId, answers)
        setQuizResult(result)

        result.newly_unlocked_achievements.forEach((achievement) => {
          pushToast(
            achievement.title,
            achievement.description,
            achievement.icon,
          )
        })

        setNodeDetail((current) =>
          current !== null && current.id === selectedNodeId
            ? { ...current, status: result.node_status }
            : current,
        )

        const [freshGraph, courseList, achievementList] = await Promise.all([
          activeCourseId !== null
            ? getCourseGraph(activeCourseId)
            : Promise.resolve(null),
          getCourses(),
          getAchievements(),
        ])

        if (freshGraph !== null) setGraph(freshGraph)
        setCourses(courseList)
        setAchievements(achievementList)
        // Metrics pas ophalen nadat de graaf-call zijn teller heeft verhoogd.
        setMetrics(await getMetrics())
      } catch (error) {
        pushToast('Inzending mislukt', errorMessage(error), 'Sparkles')
      } finally {
        setSubmitting(false)
      }
    },
    [activeCourseId, pushToast, selectedNodeId],
  )

  const retryQuiz = useCallback(async () => {
    if (selectedNodeId === null) return
    setQuizResult(null)
    setNodeLoading(true)
    try {
      const detail = await getNode(selectedNodeId)
      setNodeDetail(detail)
      setMetrics(await getMetrics())
    } catch (error) {
      pushToast('Nieuwe poging laden mislukt', errorMessage(error), 'Sparkles')
    } finally {
      setNodeLoading(false)
    }
  }, [pushToast, selectedNodeId])

  const handleDeleteCourse = useCallback(
    async (courseId: number) => {
      try {
        await deleteCourse(courseId)
        const remaining = await getCourses()
        setCourses(remaining)
        setAchievements(await getAchievements())
        setMetrics(await getMetrics())

        if (activeCourseId === courseId) {
          setActiveCourseId(null)
          setGraph(null)
          closeDrawer()
          if (remaining.length > 0) {
            await selectCourse(remaining[0].id)
          }
        }
      } catch (error) {
        pushToast('Vak verwijderen mislukt', errorMessage(error), 'Sparkles')
      }
    },
    [activeCourseId, closeDrawer, pushToast, selectCourse],
  )

  const handleCreated = useCallback(
    async (course: CourseSummary) => {
      setCreateOpen(false)
      try {
        setCourses(await getCourses())
        await selectCourse(course.id)
      } catch (error) {
        pushToast('Nieuw vak laden mislukt', errorMessage(error), 'Sparkles')
      }
    },
    [pushToast, selectCourse],
  )

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50">
      <Sidebar
        open={sidebarOpen}
        onToggle={() => setSidebarOpen((current) => !current)}
        courses={courses}
        activeCourseId={activeCourseId}
        achievements={achievements}
        onSelectCourse={(courseId) => void selectCourse(courseId)}
        onCreateCourse={() => setCreateOpen(true)}
        onDeleteCourse={(courseId) => void handleDeleteCourse(courseId)}
        onShowAchievements={() => setAchievementsOpen(true)}
      />

      <main className="relative flex-1 overflow-hidden">
        {graphLoading && graph === null ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-slate-400">
            <Loader2 size={24} className="animate-spin text-indigo-500" />
            <p className="text-xs">Graaf laden…</p>
          </div>
        ) : graph !== null ? (
          <GraphCanvas
            graph={graph}
            metrics={metrics}
            selectedNodeId={selectedNodeId}
            onNodeSelect={(nodeId) => void openNode(nodeId)}
          />
        ) : (
          <EmptyState onCreate={() => setCreateOpen(true)} />
        )}

        {graphLoading && graph !== null && (
          <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center bg-slate-50/40">
            <Loader2 size={22} className="animate-spin text-indigo-500" />
          </div>
        )}

        {selectedNodeId !== null && (
          <div className="absolute inset-y-0 right-0 z-20 h-full">
            <NodeDrawer
              node={nodeDetail}
              loading={nodeLoading}
              submitting={submitting}
              result={quizResult}
              onClose={closeDrawer}
              onSelectNode={(nodeId) => void openNode(nodeId)}
              onSubmit={(answers) => void handleSubmit(answers)}
              onRetry={() => void retryQuiz()}
            />
          </div>
        )}
      </main>

      <CreateCourseModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(course) => void handleCreated(course)}
      />

      <AchievementsModal
        open={achievementsOpen}
        achievements={achievements}
        onClose={() => setAchievementsOpen(false)}
      />

      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  )
}

function EmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 text-center">
      <div className="grid h-16 w-16 place-items-center rounded-2xl bg-indigo-50 text-indigo-500">
        <Layers size={30} />
      </div>
      <h2 className="mt-4 text-lg font-semibold text-slate-800">
        Nog geen vak geselecteerd
      </h2>
      <p className="mt-1 max-w-sm text-sm leading-relaxed text-slate-500">
        Maak een vak aan op basis van een PDF of PPTX, of kies een bestaand vak
        in de zijbalk.
      </p>
      <button
        type="button"
        onClick={onCreate}
        className="mt-5 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 active:scale-[0.99]"
      >
        <Plus size={16} />
        Nieuw vak aanmaken
      </button>
    </div>
  )
}
