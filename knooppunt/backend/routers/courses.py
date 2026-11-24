"""Endpoints voor vakken: lijst, aanmaken (multipart), verwijderen en graaf."""

from __future__ import annotations

import json
import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from ai_service import AIServiceError, generate_course_graph
from config import settings
from database import get_db
from docs2md import process_file
from graph_engine import bump_zero_ai, compute_initial_statuses
from models import Course, Edge, Node, Question
from schemas import CourseGraphOut, CourseSummary

router = APIRouter(prefix="/api", tags=["courses"])

ALLOWED_EXTENSIONS = {".pdf", ".pptx"}


def _course_counts(course_id: int, db: Session) -> tuple[int, int, float]:
    total = (
        db.query(func.count(Node.id))
        .filter(Node.course_id == course_id)
        .scalar()
        or 0
    )
    completed = (
        db.query(func.count(Node.id))
        .filter(Node.course_id == course_id, Node.status == "completed")
        .scalar()
        or 0
    )
    progress = round((completed / total) * 100, 1) if total else 0.0
    return total, completed, progress


def _summary(course: Course, db: Session) -> dict:
    total, completed, progress = _course_counts(course.id, db)
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description or "",
        "source_filenames": json.loads(course.source_filenames or "[]"),
        "total_nodes": total,
        "completed_nodes": completed,
        "progress_percentage": progress,
        "raw_tokens_est": course.raw_tokens_est or 0,
        "clean_tokens_est": course.clean_tokens_est or 0,
        "created_at": course.created_at,
    }


@router.get("/courses", response_model=list[CourseSummary])
def list_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).order_by(Course.id.asc()).all()
    return [_summary(course, db) for course in courses]


@router.post("/courses", response_model=CourseSummary, status_code=201)
def create_course(
    title: str = Form(...),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    title = (title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Vul een vaknaam in.")
    if len(title) > 200:
        raise HTTPException(
            status_code=400, detail="De vaknaam mag maximaal 200 tekens bevatten."
        )
    if not files:
        raise HTTPException(
            status_code=400,
            detail="Voeg minstens één PDF- of PPTX-bestand toe.",
        )

    markdown_parts: list[str] = []
    filenames: list[str] = []
    raw_tokens_total = 0
    clean_tokens_total = 0

    try:
        for upload in files:
            filename = upload.filename or "bestand"
            extension = os.path.splitext(filename)[1].lower()
            if extension not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Bestandstype '{extension or 'onbekend'}' wordt niet "
                        "ondersteund. Gebruik .pdf of .pptx."
                    ),
                )
            file_bytes = upload.file.read()
            try:
                result = process_file(
                    file_bytes,
                    filename,
                    db,
                    repeat_threshold=settings.DOCS_REPEAT_THRESHOLD,
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

            markdown_parts.append(result["clean_markdown"])
            filenames.append(filename)
            raw_tokens_total += int(result["raw_tokens_est"])
            clean_tokens_total += int(result["clean_tokens_est"])

        combined_markdown = "\n\n".join(markdown_parts)

        try:
            graph = generate_course_graph(title, combined_markdown, db)
        except AIServiceError as exc:
            raise HTTPException(
                status_code=exc.status_code, detail=exc.message
            ) from exc

        course = Course(
            title=title,
            description=graph.get("description") or "",
            source_filenames=json.dumps(filenames, ensure_ascii=False),
            raw_tokens_est=raw_tokens_total,
            clean_tokens_est=clean_tokens_total,
        )
        db.add(course)
        db.flush()

        key_to_node: dict[str, Node] = {}
        for node_data in graph["nodes"]:
            node = Node(
                course_id=course.id,
                temp_key=node_data["temp_key"],
                title=node_data["title"],
                summary=node_data["summary"],
                key_points=json.dumps(
                    node_data["key_points"], ensure_ascii=False
                ),
                status="locked",
            )
            db.add(node)
            db.flush()
            key_to_node[node_data["temp_key"]] = node

            for question_data in node_data["core_questions"]:
                db.add(
                    Question(
                        node_id=node.id,
                        linked_node_id=None,
                        category="core_80",
                        question_type="mcq",
                        prompt=question_data["prompt"],
                        options=json.dumps(
                            question_data["options"], ensure_ascii=False
                        ),
                        correct_answer=question_data["correct_answer"],
                        explanation=question_data["explanation"],
                    )
                )

        for edge_data in graph["edges"]:
            source = key_to_node.get(edge_data["source"])
            target = key_to_node.get(edge_data["target"])
            if source is None or target is None:
                continue
            db.add(
                Edge(
                    course_id=course.id,
                    source_node_id=source.id,
                    target_node_id=target.id,
                    relation_label=edge_data.get("relation_label")
                    or "bouwt voort op",
                )
            )

        db.flush()
        compute_initial_statuses(course.id, db)
        db.commit()
        db.refresh(course)
        return _summary(course, db)

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Vak niet gevonden.")
    db.delete(course)
    db.commit()
    return {"deleted": True}


@router.get("/courses/{course_id}/graph", response_model=CourseGraphOut)
def get_course_graph(course_id: int, db: Session = Depends(get_db)):
    bump_zero_ai(db)
    course = db.get(Course, course_id)
    if course is None:
        db.rollback()
        raise HTTPException(status_code=404, detail="Vak niet gevonden.")

    nodes = (
        db.query(Node)
        .filter(Node.course_id == course_id)
        .order_by(Node.id.asc())
        .all()
    )
    edges = (
        db.query(Edge)
        .filter(Edge.course_id == course_id)
        .order_by(Edge.id.asc())
        .all()
    )
    total, completed, progress = _course_counts(course_id, db)

    payload = {
        "course": {
            "id": course.id,
            "title": course.title,
            "total_nodes": total,
            "completed_nodes": completed,
            "progress_percentage": progress,
        },
        "nodes": [
            {
                "id": node.id,
                "title": node.title,
                "status": node.status,
                "pos_x": node.pos_x or 0.0,
                "pos_y": node.pos_y or 0.0,
            }
            for node in nodes
        ],
        "edges": [
            {
                "id": edge.id,
                "source_node_id": edge.source_node_id,
                "target_node_id": edge.target_node_id,
                "relation_label": edge.relation_label or "bouwt voort op",
            }
            for edge in edges
        ],
    }
    db.commit()
    return payload
