"""SQLAlchemy ORM-modellen — exact de 8 tabellen uit de specificatie."""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


def utcnow() -> datetime:
    """Naïeve UTC-tijd (SQLite bewaart geen tijdzone)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    source_filenames = Column(Text, default="[]")
    raw_tokens_est = Column(Integer, default=0)
    clean_tokens_est = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    nodes = relationship(
        "Node",
        back_populates="course",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    edges = relationship(
        "Edge",
        back_populates="course",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    temp_key = Column(String(64), nullable=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=False)
    key_points = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="locked")
    difficulty = Column(Integer, nullable=False, default=3)
    content_volume = Column(Integer, nullable=False, default=3)
    pos_x = Column(Float, default=0.0)
    pos_y = Column(Float, default=0.0)
    completed_at = Column(DateTime, nullable=True)

    course = relationship("Course", back_populates="nodes")
    questions = relationship(
        "Question",
        foreign_keys="Question.node_id",
        back_populates="node",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    attempts = relationship(
        "QuizAttempt",
        back_populates="node",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Edge(Base):
    __tablename__ = "edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    source_node_id = Column(
        Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    target_node_id = Column(
        Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    relation_label = Column(String(120), default="bouwt voort op")

    course = relationship("Course", back_populates="edges")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(
        Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    linked_node_id = Column(
        Integer, ForeignKey("nodes.id", ondelete="SET NULL"), nullable=True
    )
    category = Column(String(20), nullable=False)
    question_type = Column(String(20), nullable=False)
    prompt = Column(Text, nullable=False)
    options = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)

    node = relationship(
        "Node", foreign_keys=[node_id], back_populates="questions"
    )
    linked_node = relationship("Node", foreign_keys=[linked_node_id])


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(
        Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    score_percentage = Column(Float, nullable=False)
    passed = Column(Boolean, nullable=False)
    bridge_correct = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    node = relationship("Node", back_populates="attempts")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(50), nullable=False)
    unlocked_at = Column(DateTime, nullable=True)


class DocumentCache(Base):
    __tablename__ = "document_cache"

    file_hash = Column(String(64), primary_key=True)
    filename = Column(String(255), nullable=False)
    clean_markdown = Column(Text, nullable=False)
    speaker_notes = Column(Text, default="")
    raw_tokens_est = Column(Integer, nullable=False)
    clean_tokens_est = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=utcnow)


class UsageMetric(Base):
    __tablename__ = "usage_metrics"

    id = Column(Integer, primary_key=True, default=1)
    layer1_calls = Column(Integer, default=0)
    layer3_calls = Column(Integer, default=0)
    zero_ai_actions = Column(Integer, default=0)
    tokens_saved_est = Column(Integer, default=0)
