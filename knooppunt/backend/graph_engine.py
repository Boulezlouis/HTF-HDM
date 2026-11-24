"""Laag 2 — 100% deterministische graaflogica (0 AI).

Bevat statusbeheer, de 80/20-quizselectie met BFS over voorgangers, de
quizbeoordeling en alle vijf achievement-condities.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from ai_service import (
    AIServiceError,
    evaluate_open_answer_or_hint,
    generate_bridge_question,
)
from models import (
    Achievement,
    Edge,
    Node,
    Question,
    QuizAttempt,
    UsageMetric,
    utcnow,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def bump_zero_ai(db: Session) -> None:
    """Elke deterministische actie vanuit een endpoint telt als 'zonder AI'."""
    metric = db.get(UsageMetric, 1)
    if metric is None:
        metric = UsageMetric(
            id=1,
            layer1_calls=0,
            layer3_calls=0,
            zero_ai_actions=0,
            tokens_saved_est=0,
        )
        db.add(metric)
        db.flush()
    metric.zero_ai_actions = (metric.zero_ai_actions or 0) + 1


# ---------------------------------------------------------------------------
# 7.1 — initiële statussen
# ---------------------------------------------------------------------------


def compute_initial_statuses(course_id: int, db: Session) -> None:
    nodes = (
        db.query(Node)
        .filter(Node.course_id == course_id)
        .order_by(Node.id.asc())
        .all()
    )
    if not nodes:
        return

    incoming_counts = dict(
        db.query(Edge.target_node_id, func.count(Edge.id))
        .filter(Edge.course_id == course_id)
        .group_by(Edge.target_node_id)
        .all()
    )

    for node in nodes:
        node.status = "available" if incoming_counts.get(node.id, 0) == 0 else "locked"

    # Veiligheidsnet: een vreemde graaf mag nooit volledig op slot blijven.
    if not any(node.status == "available" for node in nodes):
        nodes[0].status = "available"

    db.flush()


# ---------------------------------------------------------------------------
# 7.2 — ontgrendelen na slagen
# ---------------------------------------------------------------------------


def unlock_dependent_nodes(completed_node: Node, db: Session) -> list[int]:
    """Zet directe opvolgers op 'available' zodra álle voorgangers klaar zijn."""
    unlocked: list[int] = []
    outgoing = (
        db.query(Edge)
        .filter(Edge.source_node_id == completed_node.id)
        .order_by(Edge.id.asc())
        .all()
    )

    for edge in outgoing:
        target = db.get(Node, edge.target_node_id)
        if target is None or target.status != "locked":
            continue

        predecessor_ids = [
            row.source_node_id
            for row in db.query(Edge)
            .filter(Edge.target_node_id == target.id)
            .all()
        ]
        if not predecessor_ids:
            continue

        predecessors = (
            db.query(Node).filter(Node.id.in_(predecessor_ids)).all()
        )
        if all(pred.status == "completed" for pred in predecessors):
            target.status = "available"
            unlocked.append(target.id)

    db.flush()
    return unlocked


# ---------------------------------------------------------------------------
# 7.3 — 80/20-quizselectie
# ---------------------------------------------------------------------------


def _find_completed_predecessor(
    node: Node, db: Session
) -> tuple[Node | None, str | None]:
    """BFS achteruit: bij voorkeur een voltooide voorganger op afstand 1."""
    incoming = (
        db.query(Edge)
        .filter(Edge.target_node_id == node.id)
        .order_by(Edge.id.asc())
        .all()
    )

    for edge in incoming:
        predecessor = db.get(Node, edge.source_node_id)
        if predecessor is not None and predecessor.status == "completed":
            return predecessor, edge.relation_label

    for edge in incoming:
        predecessor = db.get(Node, edge.source_node_id)
        if predecessor is None:
            continue
        for second_edge in (
            db.query(Edge)
            .filter(Edge.target_node_id == predecessor.id)
            .order_by(Edge.id.asc())
            .all()
        ):
            second = db.get(Node, second_edge.source_node_id)
            if (
                second is not None
                and second.id != node.id
                and second.status == "completed"
            ):
                return second, second_edge.relation_label

    return None, None


def _select_core_questions(
    core_questions: list[Question], limit: int, attempt_count: int
) -> list[Question]:
    """Deterministisch, maar roterend bij herkansingen."""
    if not core_questions:
        return []
    take = min(limit, len(core_questions))
    start = (attempt_count * take) % len(core_questions)
    return [
        core_questions[(start + offset) % len(core_questions)]
        for offset in range(take)
    ]


def build_80_20_quiz(node_id: int, db: Session) -> list[Question]:
    """4 kernvragen + 1 (gecachte of nieuwe) brugvraag, of 5 kernvragen."""
    node = db.get(Node, node_id)
    if node is None:
        raise ValueError("Knoop niet gevonden.")

    core_questions = (
        db.query(Question)
        .filter(
            Question.node_id == node_id,
            Question.category == "core_80",
        )
        .order_by(Question.id.asc())
        .all()
    )

    predecessor, relation_hint = _find_completed_predecessor(node, db)
    bridge: Question | None = None

    if predecessor is not None:
        # Cache-check vóór elke AI-call.
        bridge = (
            db.query(Question)
            .filter(
                Question.node_id == node_id,
                Question.category == "bridge_20",
                Question.linked_node_id == predecessor.id,
            )
            .order_by(Question.id.asc())
            .first()
        )

        if bridge is None:
            try:
                data = generate_bridge_question(
                    predecessor, node, relation_hint or "bouwt voort op", db
                )
                bridge = Question(
                    node_id=node_id,
                    linked_node_id=predecessor.id,
                    category="bridge_20",
                    question_type="mcq",
                    prompt=data["prompt"],
                    options=json.dumps(data["options"], ensure_ascii=False),
                    correct_answer=data["correct_answer"],
                    explanation=data["explanation"],
                )
                db.add(bridge)
                db.flush()
            except AIServiceError as exc:
                if exc.status_code == 400:
                    # Geen Laag 3-key geconfigureerd: de demo blijft werken met
                    # een quiz van 5 kernvragen (geen AI-call gemaakt).
                    logger.warning(
                        "Geen Laag 3-key; quiz voor knoop %s zonder brugvraag.",
                        node_id,
                    )
                    bridge = None
                else:
                    raise

    attempt_count = (
        db.query(func.count(QuizAttempt.id))
        .filter(QuizAttempt.node_id == node_id)
        .scalar()
        or 0
    )

    limit = 4 if bridge is not None else 5
    quiz = _select_core_questions(core_questions, limit, attempt_count)
    if bridge is not None:
        quiz.append(bridge)
    return quiz


def get_prerequisites(node_id: int, db: Session) -> list[dict[str, object]]:
    edges = (
        db.query(Edge)
        .filter(Edge.target_node_id == node_id)
        .order_by(Edge.id.asc())
        .all()
    )
    prerequisites: list[dict[str, object]] = []
    for edge in edges:
        predecessor = db.get(Node, edge.source_node_id)
        if predecessor is not None:
            prerequisites.append(
                {
                    "id": predecessor.id,
                    "title": predecessor.title,
                    "status": predecessor.status,
                }
            )
    prerequisites.sort(key=lambda item: int(item["id"]))  # type: ignore[arg-type]
    return prerequisites


# ---------------------------------------------------------------------------
# 7.4 — beoordeling
# ---------------------------------------------------------------------------


def grade_quiz(
    node_id: int, answers: list[dict[str, object]], db: Session
) -> dict[str, object]:
    node = db.get(Node, node_id)
    if node is None:
        raise ValueError("Knoop niet gevonden.")
    if not answers:
        raise ValueError("Geen antwoorden ontvangen.")

    results: list[dict[str, object]] = []
    correct_count = 0
    total = 0
    bridge_correct: bool | None = None

    for item in answers:
        question_id = int(item.get("question_id"))  # type: ignore[arg-type]
        question = db.get(Question, question_id)
        if question is None or question.node_id != node_id:
            continue

        total += 1
        user_answer = str(item.get("answer") or "").strip()

        if question.question_type == "short_open":
            evaluation = evaluate_open_answer_or_hint(
                question, user_answer, node, db
            )
            is_correct = bool(evaluation["is_correct"])
            explanation = str(evaluation.get("feedback") or question.explanation)
        else:
            is_correct = user_answer == question.correct_answer.strip()
            explanation = question.explanation

        if is_correct:
            correct_count += 1
        if question.category == "bridge_20":
            bridge_correct = is_correct

        results.append(
            {
                "question_id": question.id,
                "is_correct": is_correct,
                "correct_answer": question.correct_answer,
                "explanation": explanation,
            }
        )

    if total == 0:
        raise ValueError("Geen geldige vragen in de inzending.")

    score_percentage = round((correct_count / total) * 100, 1)
    passed = score_percentage >= 80.0

    attempt = QuizAttempt(
        node_id=node_id,
        score_percentage=score_percentage,
        passed=passed,
        bridge_correct=bridge_correct,
    )
    db.add(attempt)
    db.flush()

    unlocked_node_ids: list[int] = []
    if passed:
        node.status = "completed"
        node.completed_at = utcnow()
        unlocked_node_ids = unlock_dependent_nodes(node, db)

    newly_unlocked = check_and_unlock_achievements(db, node.course_id, attempt)
    db.commit()

    return {
        "score_percentage": score_percentage,
        "passed": passed,
        "node_status": node.status,
        "results": results,
        "unlocked_node_ids": unlocked_node_ids,
        "newly_unlocked_achievements": newly_unlocked,
    }


# ---------------------------------------------------------------------------
# 7.5 — deterministische achievements
# ---------------------------------------------------------------------------


def _has_full_completed_path(db: Session, course_id: int) -> bool:
    """Bestaat er een volledig groen pad van startknoop naar eindknoop (>= 2)?"""
    nodes = db.query(Node).filter(Node.course_id == course_id).all()
    if not nodes:
        return False
    edges = db.query(Edge).filter(Edge.course_id == course_id).all()

    by_id = {node.id: node for node in nodes}
    outgoing: dict[int, list[int]] = defaultdict(list)
    incoming: dict[int, list[int]] = defaultdict(list)
    for edge in edges:
        outgoing[edge.source_node_id].append(edge.target_node_id)
        incoming[edge.target_node_id].append(edge.source_node_id)

    starts = [node.id for node in nodes if not incoming[node.id]]
    ends = {node.id for node in nodes if not outgoing[node.id]}

    for start in starts:
        start_node = by_id[start]
        if start_node.status != "completed":
            continue
        stack: list[tuple[int, list[int]]] = [(start, [start])]
        while stack:
            current, path = stack.pop()
            if current in ends and len(path) >= 2:
                return True
            for nxt in outgoing[current]:
                nxt_node = by_id.get(nxt)
                if (
                    nxt_node is not None
                    and nxt_node.status == "completed"
                    and nxt not in path
                ):
                    stack.append((nxt, path + [nxt]))
    return False


def check_and_unlock_achievements(
    db: Session, course_id: int, attempt: QuizAttempt
) -> list[dict[str, str]]:
    """Controleert alle 5 condities en retourneert enkel nieuw ontgrendelde."""
    db.flush()
    achievements = {row.code: row for row in db.query(Achievement).all()}
    newly_unlocked: list[dict[str, str]] = []

    def unlock(code: str) -> None:
        achievement = achievements.get(code)
        if achievement is not None and achievement.unlocked_at is None:
            achievement.unlocked_at = utcnow()
            db.flush()
            newly_unlocked.append(
                {
                    "code": achievement.code,
                    "title": achievement.title,
                    "description": achievement.description,
                    "icon": achievement.icon,
                }
            )

    # 1. FIRST_FOUNDATION — minstens één knoop ooit afgerond.
    first_completed = (
        db.query(Node).filter(Node.status == "completed").first()
    )
    if first_completed is not None:
        unlock("FIRST_FOUNDATION")

    # 2. BRIDGE_BUILDER — laatste 3 brugvragen (met resultaat) allemaal juist.
    last_three = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.bridge_correct.isnot(None))
        .order_by(QuizAttempt.created_at.desc(), QuizAttempt.id.desc())
        .limit(3)
        .all()
    )
    if len(last_three) == 3 and all(row.bridge_correct for row in last_three):
        unlock("BRIDGE_BUILDER")

    # 3. BRANCH_COMPLETE — volledig groen pad in het huidige vak.
    if _has_full_completed_path(db, course_id):
        unlock("BRANCH_COMPLETE")

    # 4. NO_ILLUSION — eerste poging op deze knoop met 100%.
    attempt_count = (
        db.query(func.count(QuizAttempt.id))
        .filter(QuizAttempt.node_id == attempt.node_id)
        .scalar()
        or 0
    )
    if attempt_count == 1 and attempt.score_percentage >= 100.0:
        unlock("NO_ILLUSION")

    # 5. COURSE_MASTERY — alle knopen in het vak groen.
    total_nodes = (
        db.query(func.count(Node.id))
        .filter(Node.course_id == course_id)
        .scalar()
        or 0
    )
    unfinished = (
        db.query(func.count(Node.id))
        .filter(Node.course_id == course_id, Node.status != "completed")
        .scalar()
        or 0
    )
    if total_nodes >= 1 and unfinished == 0:
        unlock("COURSE_MASTERY")

    return newly_unlocked
