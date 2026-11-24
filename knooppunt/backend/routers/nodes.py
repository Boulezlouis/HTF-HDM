"""Endpoints voor knopen: detail met 80/20-quiz en inzending/beoordeling."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ai_service import AIServiceError
from database import get_db
from graph_engine import build_80_20_quiz, bump_zero_ai, get_prerequisites, grade_quiz
from models import Node, Question
from schemas import NodeDetailOut, SubmitRequest, SubmitResultOut

router = APIRouter(prefix="/api", tags=["nodes"])


@router.get("/nodes/{node_id}", response_model=NodeDetailOut)
def get_node(node_id: int, db: Session = Depends(get_db)):
    bump_zero_ai(db)
    node = db.get(Node, node_id)
    if node is None:
        db.rollback()
        raise HTTPException(status_code=404, detail="Knoop niet gevonden.")

    try:
        quiz = build_80_20_quiz(node_id, db)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc

    prerequisites = get_prerequisites(node_id, db)

    payload = {
        "id": node.id,
        "course_id": node.course_id,
        "title": node.title,
        "summary": node.summary,
        "key_points": json.loads(node.key_points or "[]"),
        "status": node.status,
        "difficulty": node.difficulty or 3,
        "content_volume": node.content_volume or 3,
        "prerequisites": prerequisites,
        "quiz": [
            {
                "id": question.id,
                "category": question.category,
                "question_type": question.question_type,
                "linked_node_title": (
                    question.linked_node.title
                    if question.linked_node is not None
                    else None
                ),
                "prompt": question.prompt,
                "options": _parse_options(question),
            }
            for question in quiz
        ],
    }
    db.commit()
    return payload


def _parse_options(question: Question) -> list[str]:
    try:
        options = json.loads(question.options or "[]")
    except json.JSONDecodeError:
        return []
    return options if isinstance(options, list) else []


@router.post("/nodes/{node_id}/submit", response_model=SubmitResultOut)
def submit_quiz(
    node_id: int, payload: SubmitRequest, db: Session = Depends(get_db)
):
    bump_zero_ai(db)
    node = db.get(Node, node_id)
    if node is None:
        db.rollback()
        raise HTTPException(status_code=404, detail="Knoop niet gevonden.")
    if not payload.answers:
        db.rollback()
        raise HTTPException(status_code=400, detail="Geen antwoorden ontvangen.")

    answers = [
        {"question_id": answer.question_id, "answer": answer.answer}
        for answer in payload.answers
    ]
    try:
        result = grade_quiz(node_id, answers, db)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AIServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc

    return result
