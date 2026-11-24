"""Pydantic-schema's: API-contract en validatie van AI-uitvoer."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

NodeStatus = Literal["locked", "available", "completed"]
QuestionCategory = Literal["core_80", "bridge_20"]
QuestionType = Literal["mcq", "short_open"]


# ---------------------------------------------------------------------------
# API — responses
# ---------------------------------------------------------------------------


class CourseSummary(BaseModel):
    id: int
    title: str
    description: str
    source_filenames: list[str]
    total_nodes: int
    completed_nodes: int
    progress_percentage: float
    raw_tokens_est: int
    clean_tokens_est: int
    created_at: datetime


class GraphCourseInfo(BaseModel):
    id: int
    title: str
    total_nodes: int
    completed_nodes: int
    progress_percentage: float


class GraphNodeOut(BaseModel):
    id: int
    title: str
    status: NodeStatus
    pos_x: float
    pos_y: float


class GraphEdgeOut(BaseModel):
    id: int
    source_node_id: int
    target_node_id: int
    relation_label: str


class CourseGraphOut(BaseModel):
    course: GraphCourseInfo
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]


class PrerequisiteOut(BaseModel):
    id: int
    title: str
    status: NodeStatus


class QuizQuestionOut(BaseModel):
    id: int
    category: QuestionCategory
    question_type: QuestionType
    linked_node_title: str | None
    prompt: str
    options: list[str]


class NodeDetailOut(BaseModel):
    id: int
    course_id: int
    title: str
    summary: str
    key_points: list[str]
    status: NodeStatus
    prerequisites: list[PrerequisiteOut]
    quiz: list[QuizQuestionOut]


class AnswerIn(BaseModel):
    question_id: int
    answer: str = ""


class SubmitRequest(BaseModel):
    answers: list[AnswerIn]


class QuestionResultOut(BaseModel):
    question_id: int
    is_correct: bool
    correct_answer: str
    explanation: str


class AchievementInfoOut(BaseModel):
    code: str
    title: str
    description: str
    icon: str


class SubmitResultOut(BaseModel):
    score_percentage: float
    passed: bool
    node_status: NodeStatus
    results: list[QuestionResultOut]
    unlocked_node_ids: list[int]
    newly_unlocked_achievements: list[AchievementInfoOut]


class AchievementOut(BaseModel):
    code: str
    title: str
    description: str
    icon: str
    unlocked_at: datetime | None


class MetricsOut(BaseModel):
    layer1_calls: int
    layer3_calls: int
    zero_ai_actions: int
    tokens_saved_est: int


# ---------------------------------------------------------------------------
# Validatie van AI-uitvoer (Laag 1 en Laag 3)
# ---------------------------------------------------------------------------


class AICoreQuestion(BaseModel):
    prompt: str = Field(min_length=3)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer: str
    explanation: str = Field(min_length=1)

    @field_validator("prompt", "correct_answer", "explanation")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("options")
    @classmethod
    def _clean_options(cls, options: list[str]) -> list[str]:
        cleaned = [str(option).strip() for option in options]
        if any(not option for option in cleaned):
            raise ValueError("Opties mogen niet leeg zijn.")
        if len(set(cleaned)) != 4:
            raise ValueError("De vier opties moeten uniek zijn.")
        return cleaned

    @model_validator(mode="after")
    def _answer_in_options(self) -> "AICoreQuestion":
        if self.correct_answer not in self.options:
            raise ValueError("Het juiste antwoord moet letterlijk in de opties staan.")
        return self


class AINode(BaseModel):
    temp_key: str = ""
    title: str = Field(min_length=2)
    summary: str = Field(min_length=3)
    key_points: list[str] = Field(default_factory=list)
    # Vragen worden één voor één gevalideerd, zodat één slechte vraag de
    # rest van de knoop niet onbruikbaar maakt.
    core_questions: list[Any] = Field(default_factory=list)


class AIEdge(BaseModel):
    source: str
    target: str
    relation_label: str = "bouwt voort op"


class AIBridgeQuestion(BaseModel):
    prompt: str = Field(min_length=3)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer: str
    explanation: str = Field(min_length=1)

    @field_validator("prompt", "correct_answer", "explanation")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("options")
    @classmethod
    def _clean_options(cls, options: list[str]) -> list[str]:
        cleaned = [str(option).strip() for option in options]
        if any(not option for option in cleaned):
            raise ValueError("Opties mogen niet leeg zijn.")
        if len(set(cleaned)) != 4:
            raise ValueError("De vier opties moeten uniek zijn.")
        return cleaned

    @model_validator(mode="after")
    def _answer_in_options(self) -> "AIBridgeQuestion":
        if self.correct_answer not in self.options:
            raise ValueError("Het juiste antwoord moet letterlijk in de opties staan.")
        return self


class AIOpenEvaluation(BaseModel):
    is_correct: bool
    feedback: str = ""

    @field_validator("feedback")
    @classmethod
    def _strip_feedback(cls, value: str) -> str:
        return value.strip()
