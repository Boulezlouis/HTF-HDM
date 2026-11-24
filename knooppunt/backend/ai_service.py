"""AI-service: Laag 1 (eenmalige graaf-extractie) en Laag 3 (on-demand).

Beide lagen gebruiken de OpenAI-compatibele client, zodat elke provider
(DeepSeek, Gemini OpenAI-compat, OpenRouter, Ollama, ...) werkt via .env.
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from typing import Any

from openai import OpenAI
from pydantic import ValidationError
from sqlalchemy.orm import Session

from config import settings
from models import Node, Question, UsageMetric
from schemas import AIBridgeQuestion, AIOpenEvaluation

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
    "en een korte `explanation` van max 2 zinnen).\n"
    "- Per knoop: `difficulty` (geheel getal 1..5: hoe conceptueel moeilijk het "
    "onderwerp is) en `content_volume` (geheel getal 1..5: hoeveel leerstof en "
    "details dit onderwerp in het document omvat).\n"
    "Verplicht formaat (voorbeeld):\n"
    '{"description": "Korte omschrijving van het vak (1 zin)", '
    '"nodes": [{"temp_key": "n1", "title": "Korte concepttitel", '
    '"summary": "Max 3 heldere zinnen.", "key_points": ["Punt 1", "Punt 2", "Punt 3"], '
    '"difficulty": 3, "content_volume": 3, "core_questions": [{"prompt": "Vraagtekst?", '
    '"options": ["Optie A", "Optie B", "Optie C", "Optie D"], '
    '"correct_answer": "Optie A", "explanation": "Waarom Optie A juist is."}]}], '
    '"edges": [{"source": "n1", "target": "n2", "relation_label": "is voorwaarde voor"}]}'
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
    max_tokens: int | None = None,
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
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as first_error:
        # Sommige OpenAI-compatibele providers ondersteunen response_format
        # niet. Doe exact één retry zonder die parameter.
        logger.warning(
            "Eerste AI-call met response_format mislukt (%s); retry zonder.",
            first_error,
        )
        retry_kwargs = dict(kwargs)
        retry_kwargs.pop("response_format", None)
        try:
            response = client.chat.completions.create(**retry_kwargs)
        except Exception as exc:  # provider-/netwerkfout
            logger.exception("AI-call mislukt, ook zonder response_format")
            raise AIServiceError(
                f"De AI-provider gaf een fout: {exc}", status_code=503
            ) from exc

    choice = response.choices[0]
    content = choice.message.content or ""
    if getattr(choice, "finish_reason", None) == "length":
        logger.warning(
            "AI-antwoord afgekapt door max_tokens (%s tekens ontvangen); "
            "JSON wordt zo goed mogelijk hersteld.",
            len(content),
        )
    if not content.strip():
        raise AIServiceError(
            "Het AI-model gaf een leeg antwoord. Probeer het opnieuw.",
            status_code=502,
        )
    return content


def _strip_trailing_commas(text: str) -> str:
    """Verwijdert komma's vlak voor } of ] (buiten strings)."""
    out: list[str] = []
    in_str = False
    escape = False
    for i, ch in enumerate(text):
        if in_str:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
            continue
        if ch in "}]":
            j = len(out) - 1
            while j >= 0 and out[j] in " \t\r\n":
                j -= 1
            if j >= 0 and out[j] == ",":
                del out[j]
        out.append(ch)
    return "".join(out)


def _repair_truncated_json(text: str) -> str | None:
    """Herstelt een afgekapt JSON-object: knipt terug tot het laatst volledig
    afgewerkte element en sluit alle open haakjes."""
    stack: list[str] = []
    in_str = False
    escape = False
    safe_cut = -1
    safe_stack: list[str] = []
    for i, ch in enumerate(text):
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]":
            if not stack:
                break
            stack.pop()
            if not stack:
                return text[: i + 1]
            safe_cut, safe_stack = i + 1, list(stack)
        elif ch == "," and stack:
            # Alles vóór deze komma is een volledig element.
            safe_cut, safe_stack = i, list(stack)
    if safe_cut == -1:
        return None
    repaired = text[:safe_cut].rstrip().rstrip(",")
    return repaired + "".join(reversed(safe_stack))


def extract_json_object(raw_text: str) -> dict[str, Any]:
    """Haalt een JSON-object uit modeluitvoer, ook met think-blokken/fences,
    extra tekst rondom, trailing komma's of een afgekapt einde."""
    text = re.sub(r"<think\b[^>]*>.*?</think\s*>", "", raw_text, flags=re.DOTALL)
    # Onafgesloten think-blok (afgekapt): alles tot na </think> negeren kan niet,
    # dus enkel de openingstag weghalen.
    text = re.sub(r"<think\b[^>]*>", "", text)
    text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")
    text = text.replace("“", '"').replace("”", '"') if text.count('"') == 0 else text

    def _fail(reason: str) -> AIServiceError:
        logger.error(
            "%s Ruwe model-output (eerste 1500 / laatste 500 tekens): %s ... %s",
            reason,
            raw_text[:1500] or "<leeg>",
            raw_text[-500:],
        )
        return AIServiceError(
            "Het AI-model gaf geen geldig JSON-object terug. Probeer het opnieuw.",
            status_code=502,
        )

    start = text.find("{")
    if start == -1:
        raise _fail("Geen JSON-object gevonden.")
    body = text[start:]

    decoder = json.JSONDecoder()
    attempts = [body, _strip_trailing_commas(body)]
    repaired = _repair_truncated_json(_strip_trailing_commas(body))
    if repaired:
        attempts.append(repaired)

    last_error: Exception | None = None
    for idx, candidate in enumerate(attempts):
        try:
            parsed, _ = decoder.raw_decode(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        if isinstance(parsed, dict):
            if idx == 2:
                logger.warning("Afgekapte JSON hersteld; laatste onvolledige deel genegeerd.")
            return parsed
    raise _fail(f"JSON-parsefout: {last_error}.")


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


def _clamp_scale(value: Any, default: int = 3) -> int:
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(1, min(5, parsed))


def _normalize_key_points(raw_points: Any, summary: str) -> list[str]:
    points: list[str] = []
    if isinstance(raw_points, str):
        for line in raw_points.splitlines():
            cleaned = re.sub(r"^\s*[-*•]\s*", "", line).strip()
            if cleaned:
                points.append(cleaned)
    elif isinstance(raw_points, list):
        for item in raw_points:
            if isinstance(item, dict):
                text = str(
                    item.get("point") or item.get("text") or ""
                ).strip()
            else:
                text = str(item).strip()
            if text:
                points.append(text)

    if not points:
        points = [summary]
    return points[:5]


def _normalize_correct_answer(answer: Any, options: list[str]) -> str:
    raw = str(answer or "").strip()
    if raw in options:
        return raw

    lowered = {option.lower(): option for option in options}
    if raw.lower() in lowered:
        return lowered[raw.lower()]

    match = re.match(r"^\s*([A-Za-z])\s*(?:[).:\-]|$)", raw)
    if match:
        index = ord(match.group(1).lower()) - ord("a")
        if 0 <= index < len(options):
            return options[index]

    # Laatste fallback: nooit een geldige knoop weggooien om dit detail.
    return options[0]


def _normalize_core_question(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None

    prompt = str(
        raw.get("prompt") or raw.get("question") or raw.get("vraag") or ""
    ).strip()
    raw_options = raw.get("options") or raw.get("choices") or raw.get("opties") or []
    if isinstance(raw_options, dict):
        raw_options = list(raw_options.values())
    if not isinstance(raw_options, list):
        raw_options = []
    options = [str(option).strip() for option in raw_options if str(option).strip()]

    if not prompt or len(options) < 2:
        logger.warning(
            "Kernvraag overgeslagen (prompt of opties ontbreken): %s", raw
        )
        return None

    correct = _normalize_correct_answer(
        raw.get("correct_answer")
        or raw.get("answer")
        or raw.get("juiste_antwoord"),
        options,
    )
    explanation = str(
        raw.get("explanation") or raw.get("uitleg") or ""
    ).strip() or "Geen uitleg beschikbaar."

    return {
        "prompt": prompt,
        "options": options,
        "correct_answer": correct,
        "explanation": explanation,
    }


def _sanitize_graph(data: dict[str, Any]) -> dict[str, Any]:
    description = str(
        data.get("description") or data.get("beschrijving") or ""
    ).strip()

    raw_nodes = data.get("nodes")
    if not isinstance(raw_nodes, list):
        raw_nodes = data.get("concepts")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        logger.error(
            "AI-uitvoer bevat geen nodes/concepts. Aanwezige sleutels: %s",
            list(data.keys()),
        )
        raise AIServiceError(
            "Het AI-model leverde geen bruikbare knopen. Probeer het opnieuw.",
            status_code=502,
        )

    nodes: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_nodes[:10]):
        if not isinstance(raw, dict):
            logger.warning("Knoop %d overgeslagen: geen JSON-object.", index)
            continue

        title = str(
            raw.get("title") or raw.get("name") or raw.get("titel") or ""
        ).strip()
        summary = str(
            raw.get("summary")
            or raw.get("description")
            or raw.get("samenvatting")
            or ""
        ).strip()
        if not title:
            logger.warning("Knoop %d overgeslagen: geen titel.", index)
            continue
        if not summary:
            summary = title

        key_points = _normalize_key_points(
            raw.get("key_points")
            or raw.get("keyPoints")
            or raw.get("kernpunten"),
            summary,
        )
        difficulty = _clamp_scale(
            raw.get("difficulty", raw.get("moeilijkheid")), 3
        )
        content_volume = _clamp_scale(
            raw.get("content_volume", raw.get("contentVolume")), 3
        )

        raw_questions = raw.get("core_questions")
        if not isinstance(raw_questions, list):
            raw_questions = raw.get("questions")
        if not isinstance(raw_questions, list):
            raw_questions = []

        questions: list[dict[str, Any]] = []
        for raw_question in raw_questions:
            normalized = _normalize_core_question(raw_question)
            if normalized is not None:
                questions.append(normalized)
            if len(questions) == 5:
                break

        if not questions:
            logger.warning(
                "Knoop '%s' overgeslagen: geen geldige vragen.", title
            )
            continue

        temp_key = str(
            raw.get("temp_key")
            or raw.get("id")
            or raw.get("key")
            or f"n{index + 1}"
        ).strip() or f"n{index + 1}"

        nodes.append(
            {
                "temp_key": temp_key,
                "title": title[:200],
                "summary": summary,
                "key_points": key_points,
                "difficulty": difficulty,
                "content_volume": content_volume,
                "core_questions": questions,
            }
        )

    if not nodes:
        logger.error(
            "Na normalisatie bleven 0 bruikbare knopen over van %d ruwe knopen.",
            len(raw_nodes),
        )
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
        logger.warning("Laag 1 leverde %d knopen (gevraagd: 5-10).", len(nodes))

    raw_edges = data.get("edges")
    if not isinstance(raw_edges, list):
        raw_edges = data.get("relations")

    return {
        "description": description,
        "nodes": nodes,
        "edges": _sanitize_edges(nodes, raw_edges),
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
        "Geef nu het JSON-object met description, nodes (met difficulty en "
        "content_volume), edges en core_questions."
    )

    content = ""
    try:
        data: dict[str, Any] | None = None
        for attempt in range(2):
            content = _chat_json(
                client,
                settings.LAYER1_MODEL,
                LAYER1_SYSTEM_PROMPT,
                user_prompt
                if attempt == 0
                else user_prompt
                + "\n\nLET OP: je vorige antwoord was geen geldig JSON. Antwoord "
                "nu ENKEL met het JSON-object, zonder uitleg, en houd de "
                "explanations kort.",
                temperature=0.2,
                max_tokens=16384,
            )
            _increment_metric(db, "layer1_calls")
            try:
                data = extract_json_object(content)
                break
            except AIServiceError:
                if attempt == 1:
                    raise
                logger.warning("Laag 1: ongeldige JSON, één herkansing.")
        return _sanitize_graph(data or {})
    except AIServiceError:
        logger.error(
            "Laag 1 mislukt. Ruwe model-output (eerste 1500 tekens): %s",
            (content or "<leeg>")[:1500],
        )
        raise
    except Exception as exc:
        logger.error("Onverwachte fout in Laag 1: %s", exc, exc_info=True)
        logger.error(
            "Ruwe model-output (eerste 1500 tekens): %s",
            (content or "<leeg>")[:1500],
        )
        raise AIServiceError(
            "Het AI-model leverde geen bruikbare knopen. Probeer het opnieuw.",
            status_code=502,
        ) from exc


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
    data = extract_json_object(content)

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
    data = extract_json_object(content)

    try:
        evaluation = AIOpenEvaluation.model_validate(data)
    except ValidationError as exc:
        logger.warning("Ongeldige beoordeling: %s", exc)
        raise AIServiceError(
            "Het redeneermodel leverde een ongeldige beoordeling. Probeer het opnieuw.",
            status_code=502,
        ) from exc

    return evaluation.model_dump()
