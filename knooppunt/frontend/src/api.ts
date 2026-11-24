// Fetch-wrappers voor alle REST-endpoints.

import type {
  Achievement,
  AnswerInput,
  CourseGraph,
  CourseSummary,
  Metrics,
  NodeDetail,
  SubmitResult,
} from './types'

const API_BASE = '/api'

async function extractError(response: Response): Promise<string> {
  try {
    const data: unknown = await response.json()
    if (typeof data === 'object' && data !== null && 'detail' in data) {
      const detail = (data as { detail: unknown }).detail
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail)) {
        return detail
          .map((item) =>
            typeof item === 'object' && item !== null && 'msg' in item
              ? String((item as { msg: unknown }).msg)
              : String(item),
          )
          .join(', ')
      }
    }
    return `Er ging iets mis (HTTP ${response.status}).`
  } catch {
    return `Er ging iets mis (HTTP ${response.status}).`
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, init)
  } catch {
    throw new Error(
      'Geen verbinding met de backend. Draait uvicorn op poort 8000?',
    )
  }
  if (!response.ok) {
    throw new Error(await extractError(response))
  }
  return (await response.json()) as T
}

export function getCourses(): Promise<CourseSummary[]> {
  return request<CourseSummary[]>('/courses')
}

export function createCourse(
  title: string,
  files: File[],
): Promise<CourseSummary> {
  const formData = new FormData()
  formData.append('title', title)
  files.forEach((file) => formData.append('files', file))
  return request<CourseSummary>('/courses', {
    method: 'POST',
    body: formData,
  })
}

export function deleteCourse(courseId: number): Promise<{ deleted: boolean }> {
  return request<{ deleted: boolean }>(`/courses/${courseId}`, {
    method: 'DELETE',
  })
}

export function getCourseGraph(courseId: number): Promise<CourseGraph> {
  return request<CourseGraph>(`/courses/${courseId}/graph`)
}

export function getNode(nodeId: number): Promise<NodeDetail> {
  return request<NodeDetail>(`/nodes/${nodeId}`)
}

export function submitQuiz(
  nodeId: number,
  answers: AnswerInput[],
): Promise<SubmitResult> {
  return request<SubmitResult>(`/nodes/${nodeId}/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers }),
  })
}

export function getAchievements(): Promise<Achievement[]> {
  return request<Achievement[]>('/achievements')
}

export function getMetrics(): Promise<Metrics> {
  return request<Metrics>('/metrics')
}
