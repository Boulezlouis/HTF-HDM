"""AI-service: Laag 1 (eenmalige graaf-extractie) en Laag 3 (on-demand).

Beide lagen gebruiken de OpenAI-compatibele client, zodat elke provider
(DeepSeek, Gemini OpenAI-compat, OpenRouter, Ollama, ...) werkt via .env.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from typing import Any

from openai import OpenAI
from pydantic import ValidationError
from sqlalchemy.orm import Session

from config import settings
from models import Node, Question, UsageMetric
from schemas import AIBridgeQuestion, AICoreQuestion, AINode, AIOpenEvaluation

logger = logging.getLogger(__name__)

MAX_MARKDOWN_CHARS = 60_000

LAYER1_SYSTEM_PROMPT = (
    "Je bent een onderwijskundig curriculum-architect. Zet het aangeleverde "
    "cursusmateriaal in het Nederlands om in een compacte, gerichte Knowledge "
    "Graph (DAG zonder cycli). Geef UITSLUITEND geldig JSON terug zonder extra tekst.\n"
    "Regels:\n"
    "- Maak tussen 5 en 10 kernconcepten (`nodes`), afhankelijk van de inhoud.\n"
    "- Leg gerichte afhankelijkheden (`edges`) van basisconcept (`source`) naar "
    "vervolgconcept (`target`), zonder cycli. Minstens 1 knoop heeft geen "
    "inkomende edges (startknoop).\n"
    "- Per knoop: een korte, scanbare `summary` (max 3 zinnen) en 3 tot 5 "
    "`key_points`.\n"
    "- Per knoop: exact 5 `core_questions` (meerkeuzevragen `mcq` met 4 opties, "
    "exact 1 juist antwoord dat letterlijk overeenkomt met een van de 4 opties, "
    "en een korte `explanation` van max 2 zinnen)."
)

LAYER3_BRIDGE_SYSTEM_PROMPT = (
    "Je bent een kritische examinator. Maak in het Nederlands exact EEN "
    "verbindingsvraag (`mcq` met 4 opties) die toetst of de student begrijpt hoe "
    "het vorige concept (`prev_node`) direct samenhangt met of invloed heeft op "
    "het huidige concept (`curr_node`). Vermijd triviale definitievragen; toets "
    "inzicht in het verband. Geef UITSLUITEND geldig JSON terug:\n"
    '{"prompt": "...", "options": ["...", "...", "...", "..."], '
    '"correct_answer": "...", "explanation": "..."}'
)

LAYER3_EVALUATE_SYSTEM_PROMPT = (
    "Je bent een beoordelaar van korte open antwoorden in het onderwijs. "
    "Vergelijk het antwoord van de student met het modelantwoord en beoordeel of "
    "de kern van de redenering overeenkomt; parafraseren is toegestaan. Geef "
    "UITSLUITEND geldig JSON terug:\n"
    '{"is_correct": true, "feedback": "Korte, gerichte uitleg waarom de redenering '
    'klopt of waar de denkfout zit (max 2 zinnen)."}'
)


class AIServiceError(Exception):
    """Fout met een HTTP-status die routers één-op-één kunnen doorgeven."""

    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Hulpjes
# ---------------------------------------------------------------------------


def _is_placeholder(key: str | None) -> bool:
    return (
        key is None
        or not key.strip()
        or key.strip().lower() in {"your_api_key_here", "changeme", "none"}
    )


def _check_key(key: str | None, layer: str) -> None:
    if _is_placeholder(key):
        raise AIServiceError(
            f"{layer}_API_KEY ontbreekt of staat nog op 'your_api_key_here'. "
            f"Stel {layer}_API_KEY in via je .env-bestand om een nieuw vak aan "
            "te maken.",
            status_code=400,
        )


def _make_client(base_url: str, api_key: str) -> OpenAI:
    return OpenAI(base_url=base_url, api_key=api_key)


def _increment_metric(db: Session, field: str) -> None:
    """Verhoogt een teller direct na een effectieve API-call."""
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
    setattr(metric, field, (getattr(metric, field) or 0) + 1)
    db.commit()


def _chat_json(
    client: OpenAI,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float | None = None,
) -> str:
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    if temperature is not None:
        kwargs["temperature"] = temperature

    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as exc:  # provider-/netwerkfout
        logger.exception("AI-call mislukt")
        raise AIServiceError(
            f"De AI-provider gaf een fout: {exc}", status_code=503
        ) from exc

    content = response.choices[0].message.content or ""
    if not content.strip():
        raise AIServiceError(
            "Het AI-model gaf een leeg antwoord. Probeer het opnieuw.",
            status_code=502,
        )
    return content


def _parse_json(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        # Soms omhult een model de JSON met tekst; pak het buitenste object.
        start, end = content.find("{"), content.rfind("}")
        if start != -1 and end > start:
            try:
                parsed = json.loads(content[start : end + 1])
            except json.JSONDecodeError:
                parsed = None
        else:
            parsed = None

    if not isinstance(parsed, dict):
        raise AIServiceError(
            "Het AI-model gaf geen geldig JSON-object terug. Probeer het opnieuw.",
            status_code=502,
        )
    return parsed


def _reachable(adjacency: dict[str, set[str]], start: str, goal: str) -> bool:
    stack = [start]
    seen = {start}
    while stack:
        current = stack.pop()
        if current == goal:
            return True
        for nxt in adjacency.get(current, ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return False


def _sanitize_edges(
    nodes: list[dict[str, Any]], raw_edges: Any
) -> list[dict[str, str]]:
    """Verwijdert ongeldige edges, self-loops, duplicaten en cycli."""
    keys = {node["temp_key"] for node in nodes}
    edges: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    adjacency: dict[str, set[str]] = defaultdict(set)

    if not isinstance(raw_edges, list):
        return edges

    for raw in raw_edges:
        if not isinstance(raw, dict):
            continue
        source = str(raw.get("source") or "").strip()
        target = str(raw.get("target") or "").strip()
        if source not in keys or target not in keys or source == target:
            continue
        if (source, target) in seen:
            continue
        if _reachable(adjacency, target, source):
            logger.warning("Cyclus gebroken: %s -> %s", source, target)
            continue
        seen.add((source, target))
        adjacency[source].add(target)
        label = str(raw.get("relation_label") or "bouwt voort op").strip()
        edges.append(
            {
                "source": source,
                "target": target,
                "relation_label": (label or "bouwt voort op")[:120],
            }
        )

    # Veiligheidsnet: minstens één startknoop zonder inkomende edges.
    targets = {edge["target"] for edge in edges}
    if nodes and all(node["temp_key"] in targets for node in nodes):
        first_key = nodes[0]["temp_key"]
        edges = [edge for edge in edges if edge["target"] != first_key]

    return edges


def _sanitize_graph(data: dict[str, Any]) -> dict[str, Any]:
    description = str(data.get("description") or "").strip()
    raw_nodes = data.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise AIServiceError(
            "Het AI-model leverde geen geldige knopen. Probeer het opnieuw.",
            status_code=502,
        )

    nodes: list[dict[str, Any]] = []
    for raw in raw_nodes[:10]:
        try:
            node = AINode.model_validate(raw)
        except ValidationError as exc:
            logger.warning("Ongeldige knoop overgeslagen: %s", exc)
            continue

        title = node.title.strip()
        summary = node.summary.strip()
        if not title or not summary:
            continue

        key_points = [
            str(point).strip() for point in node.key_points if str(point).strip()
        ][:5]
        if not key_points:
            key_points = [summary[:120]]

        questions: list[dict[str, Any]] = []
        for raw_question in node.core_questions:
            try:
                question = AICoreQuestion.model_validate(raw_question)
            except ValidationError as exc:
                logger.warning("Ongeldige kernvraag overgeslagen: %s", exc)
                continue
            questions.append(question.model_dump())
            if len(questions) == 5:
                break

        if not questions:
            logger.warning("Knoop '%s' overgeslagen: geen geldige vragen.", title)
            continue

        temp_key = (node.temp_key or f"n{len(nodes) + 1}").strip()
        nodes.append(
            {
                "temp_key": temp_key,
                "title": title[:200],
                "summary": summary,
                "key_points": key_points,
                "core_questions": questions,
            }
        )

    if not nodes:
        raise AIServiceError(
            "Het AI-model leverde geen bruikbare knopen. Probeer het opnieuw.",
            status_code=502,
        )

    # Unieke temp_keys garanderen.
    used_keys: set[str] = set()
    for index, node in enumerate(nodes):
        if node["temp_key"] in used_keys:
            node["temp_key"] = f"n{index + 1}x"
        while node["temp_key"] in used_keys:
            node["temp_key"] += "x"
        used_keys.add(node["temp_key"])

    if not 5 <= len(nodes) <= 10:
        logger.warning(
            "Laag 1 leverde %d knopen (gevraagd: 5-10).", len(nodes)
        )

    return {
        "description": description,
        "nodes": nodes,
        "edges": _sanitize_edges(nodes, data.get("edges")),
    }


# ---------------------------------------------------------------------------
# Laag 1 — eenmalig bij het aanmaken van een vak
# ---------------------------------------------------------------------------


def generate_course_graph(
    course_title: str, clean_markdown: str, db: Session
) -> dict[str, Any]:
    _check_key(settings.LAYER1_API_KEY, "LAYER1")
    client = _make_client(settings.LAYER1_BASE_URL, settings.LAYER1_API_KEY)

    markdown = clean_markdown
    if len(markdown) > MAX_MARKDOWN_CHARS:
        logger.warning(
            "Cursusmateriaal ingekort van %d naar %d tekens.",
            len(markdown),
            MAX_MARKDOWN_CHARS,
        )
        markdown = markdown[:MAX_MARKDOWN_CHARS]

    user_prompt = (
        f"Vak: {course_title}\n\n"
        "Cursusmateriaal:\n"
        f"{markdown}\n\n"
        "Geef nu het JSON-object met description, nodes en edges."
    )

    content = _chat_json(
        client,
        settings.LAYER1_MODEL,
        LAYER1_SYSTEM_PROMPT,
        user_prompt,
        temperature=0.2,
    )
    _increment_metric(db, "layer1_calls")
    data = _parse_json(content)
    return _sanitize_graph(data)


# ---------------------------------------------------------------------------
# Laag 3 — on-demand verbindingsvraag
# ---------------------------------------------------------------------------


def generate_bridge_question(
    prev_node: Node, curr_node: Node, relation_hint: str, db: Session
) -> dict[str, Any]:
    _check_key(settings.LAYER3_API_KEY, "LAYER3")
    client = _make_client(settings.LAYER3_BASE_URL, settings.LAYER3_API_KEY)

    # Cruciaal voor de zuinigheid: nooit de volledige cursus meesturen.
    user_prompt = (
        f"Vorig concept: {prev_node.title}\n"
        f"Samenvatting vorig concept: {prev_node.summary}\n\n"
        f"Huidig concept: {curr_node.title}\n"
        f"Samenvatting huidig concept: {curr_node.summary}\n\n"
        f"Relatie: {relation_hint}"
    )

    content = _chat_json(
        client,
        settings.LAYER3_MODEL,
        LAYER3_BRIDGE_SYSTEM_PROMPT,
        user_prompt,
    )
    _increment_metric(db, "layer3_calls")
    data = _parse_json(content)

    try:
        question = AIBridgeQuestion.model_validate(data)
    except ValidationError as exc:
        logger.warning("Ongeldige verbindingsvraag: %s", exc)
        raise AIServiceError(
            "Het redeneermodel leverde een ongeldige verbindingsvraag. "
            "Probeer het opnieuw.",
            status_code=502,
        ) from exc

    return question.model_dump()


# ---------------------------------------------------------------------------
# Laag 3 — on-demand korte-open-beoordeling of gerichte hint
# ---------------------------------------------------------------------------


def evaluate_open_answer_or_hint(
    question: Question, user_answer: str, node: Node, db: Session
) -> dict[str, Any]:
    _check_key(settings.LAYER3_API_KEY, "LAYER3")
    client = _make_client(settings.LAYER3_BASE_URL, settings.LAYER3_API_KEY)

    user_prompt = (
        f"Vraag: {question.prompt}\n"
        f"Modelantwoord: {question.correct_answer}\n"
        f"Antwoord van de student: {user_answer.strip() or '(geen antwoord)'}\n"
        f"Context (samenvatting van de knoop): {node.summary}"
    )

    content = _chat_json(
        client,
        settings.LAYER3_MODEL,
        LAYER3_EVALUATE_SYSTEM_PROMPT,
        user_prompt,
    )
    _increment_metric(db, "layer3_calls")
    data = _parse_json(content)

    try:
        evaluation = AIOpenEvaluation.model_validate(data)
    except ValidationError as exc:
        logger.warning("Ongeldige beoordeling: %s", exc)
        raise AIServiceError(
            "Het redeneermodel leverde een ongeldige beoordeling. Probeer het opnieuw.",
            status_code=502,
        ) from exc

    return evaluation.model_dump()
