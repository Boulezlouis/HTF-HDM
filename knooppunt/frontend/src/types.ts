// TypeScript-interfaces, exact gelijk aan het API-contract.

export type NodeStatus = 'locked' | 'available' | 'completed'
export type QuestionCategory = 'core_80' | 'bridge_20'
export type QuestionType = 'mcq' | 'short_open'

export interface CourseSummary {
  id: number
  title: string
  description: string
  source_filenames: string[]
  total_nodes: number
  completed_nodes: number
  progress_percentage: number
  raw_tokens_est: number
  clean_tokens_est: number
  created_at: string
}

export interface GraphCourseInfo {
  id: number
  title: string
  total_nodes: number
  completed_nodes: number
  progress_percentage: number
}

export interface GraphNode {
  id: number
  title: string
  status: NodeStatus
  pos_x: number
  pos_y: number
}

export interface GraphEdge {
  id: number
  source_node_id: number
  target_node_id: number
  relation_label: string
}

export interface CourseGraph {
  course: GraphCourseInfo
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface Prerequisite {
  id: number
  title: string
  status: NodeStatus
}

export interface QuizQuestion {
  id: number
  category: QuestionCategory
  question_type: QuestionType
  linked_node_title: string | null
  prompt: string
  options: string[]
}

export interface NodeDetail {
  id: number
  course_id: number
  title: string
  summary: string
  key_points: string[]
  status: NodeStatus
  prerequisites: Prerequisite[]
  quiz: QuizQuestion[]
}

export interface AnswerInput {
  question_id: number
  answer: string
}

export interface QuestionResult {
  question_id: number
  is_correct: boolean
  correct_answer: string
  explanation: string
}

export interface AchievementInfo {
  code: string
  title: string
  description: string
  icon: string
}

export interface SubmitResult {
  score_percentage: number
  passed: boolean
  node_status: NodeStatus
  results: QuestionResult[]
  unlocked_node_ids: number[]
  newly_unlocked_achievements: AchievementInfo[]
}

export interface Achievement {
  code: string
  title: string
  description: string
  icon: string
  unlocked_at: string | null
}

export interface Metrics {
  layer1_calls: number
  layer3_calls: number
  zero_ai_actions: number
  tokens_saved_est: number
}

export interface ToastMessage {
  id: number
  title: string
  description: string
  icon: string
}
