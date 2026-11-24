"""Lokale PDF/PPTX -> schone Markdown met SHA-256-cache (0 AI-tokens).

Gebruik als bibliotheek:
    process_file(file_bytes, filename, db)

Gebruik als CLI (vanuit de backend-map):
    python docs2md.py <bestand> --drempel 0.5
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
from typing import Any

import pdfplumber
from markitdown import MarkItDown
from sqlalchemy.orm import Session

from models import DocumentCache, UsageMetric

# ---------------------------------------------------------------------------
# Regex-patronen
# ---------------------------------------------------------------------------

IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^\)]*\)")
PAGE_NUMBER_RES = [
    re.compile(r"^\d{1,4}$"),
    re.compile(r"^(pagina|page|slide|dia)\s*\d+(\s*(van|of|/)\s*\d+)?$", re.IGNORECASE),
    re.compile(r"^\d+\s*/\s*\d+$"),
]
SLIDE_MARKER_RE = re.compile(r"<!--\s*Slide number:\s*\d+\s*-->", re.IGNORECASE)
NOTES_HEADING_RE = re.compile(
    r"(?im)^#{1,6}[ \t]*Notes[ \t]*:?[ \t]*$"
)


# ---------------------------------------------------------------------------
# Extractie
# ---------------------------------------------------------------------------


def _extract_pdf(file_bytes: bytes) -> tuple[list[str], str, str]:
    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    raw_full_text = "\n\n".join(pages)
    if len(raw_full_text.strip()) < 50:
        raise ValueError(
            "Deze PDF bevat geen tekstlaag (gescande PDF). Gebruik een tekst-PDF "
            "of zet eerst om met Docling OCR."
        )
    return pages, raw_full_text, ""


def _split_slides(text: str) -> list[str]:
    """Splits MarkItDown-uitvoer op slide-markers, --- of #-secties."""
    parts = SLIDE_MARKER_RE.split(text)
    if len(parts) > 1:
        return [part for part in parts if part.strip()]

    parts = text.split("\n---\n")
    if len(parts) > 1:
        return [part for part in parts if part.strip()]

    sections = re.split(r"(?m)^(?=#\s)", text)
    return [section for section in sections if section.strip()]


def _split_notes(page_text: str) -> tuple[str, str]:
    """Haalt een '### Notes:'-sectie uit een slide."""
    match = NOTES_HEADING_RE.search(page_text)
    if not match:
        return page_text, ""
    body = page_text[: match.start()].rstrip()
    notes = page_text[match.end() :].strip()
    return body, notes


def _extract_pptx(
    file_bytes: bytes, include_notes: bool
) -> tuple[list[str], str, str]:
    markitdown = MarkItDown(enable_plugins=False)
    result = markitdown.convert_stream(io.BytesIO(file_bytes), file_extension=".pptx")
    raw_full_text = result.text_content or ""
    if not raw_full_text.strip():
        raise ValueError("Dit PowerPoint-bestand bevat geen leesbare tekst.")

    pages: list[str] = []
    notes_parts: list[str] = []
    for page in _split_slides(raw_full_text):
        body, notes = _split_notes(page)
        if notes:
            notes_parts.append(notes)
        # Notities horen bij de presentator, niet bij de leerstof; tenzij
        # expliciet gevraagd laat je ze dus uit de hoofdtekst.
        pages.append(page if include_notes else body)

    speaker_notes = "\n\n".join(notes_parts)
    return pages, raw_full_text, speaker_notes


# ---------------------------------------------------------------------------
# Opschonen
# ---------------------------------------------------------------------------


def _strip_images(page: str) -> str:
    return IMAGE_RE.sub("", page)


def _strip_page_numbers(page: str) -> str:
    kept: list[str] = []
    for line in page.split("\n"):
        stripped = line.strip()
        if any(pattern.match(stripped) for pattern in PAGE_NUMBER_RES):
            continue
        kept.append(line)
    return "\n".join(kept)


def _is_repeated_line(line: str) -> bool:
    return bool(line.strip())


def _strip_repeated_headers(pages: list[str], repeat_threshold: float) -> list[str]:
    if len(pages) < 3:
        return pages

    page_counts: dict[str, int] = {}
    for page in pages:
        seen_on_page: set[str] = set()
        for line in page.split("\n"):
            normalized = line.strip().lower()
            if not _is_repeated_line(normalized) or normalized in seen_on_page:
                continue
            seen_on_page.add(normalized)
            page_counts[normalized] = page_counts.get(normalized, 0) + 1

    threshold = max(0.0, min(1.0, repeat_threshold))
    repeated = {
        line
        for line, count in page_counts.items()
        if count / len(pages) >= threshold
    }
    if not repeated:
        return pages

    cleaned_pages: list[str] = []
    for page in pages:
        kept = [
            line for line in page.split("\n") if line.strip().lower() not in repeated
        ]
        cleaned_pages.append("\n".join(kept))
    return cleaned_pages


def _summarize_title_page(pages: list[str]) -> list[str]:
    if not pages:
        return pages

    title_index = 0
    for index, page in enumerate(pages):
        if page.strip():
            title_index = index
            break

    lines = [line.strip() for line in pages[title_index].split("\n") if line.strip()]
    title_lines: list[str] = []
    for line in lines[:2]:
        cleaned = re.sub(r"^#{1,6}\s*", "", line).strip()
        if cleaned:
            title_lines.append(cleaned)
    context = "# Context: " + " — ".join(title_lines) if title_lines else "# Context:"

    result = list(pages)
    result[title_index] = context
    return result


def _skip_trivial_pages(pages: list[str]) -> list[str]:
    kept: list[str] = []
    for index, page in enumerate(pages):
        if index == 0 or len(re.findall(r"\w+", page)) >= 3:
            kept.append(page)
    return kept


def _compress_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Publieke API
# ---------------------------------------------------------------------------


def get_usage_metric(db: Session) -> UsageMetric:
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
    return metric


def process_file(
    file_bytes: bytes,
    filename: str,
    db: Session,
    repeat_threshold: float = 0.5,
    include_notes: bool = False,
) -> dict[str, Any]:
    """Zet PDF/PPTX om naar schone Markdown, met SHA-256-cache."""
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    cached = db.get(DocumentCache, file_hash)
    if cached is not None:
        return {
            "clean_markdown": cached.clean_markdown,
            "speaker_notes": cached.speaker_notes or "",
            "raw_tokens_est": cached.raw_tokens_est,
            "clean_tokens_est": cached.clean_tokens_est,
            "cached": True,
        }

    extension = os.path.splitext(filename)[1].lower()
    if extension == ".pdf":
        pages, raw_full_text, speaker_notes = _extract_pdf(file_bytes)
    elif extension == ".pptx":
        pages, raw_full_text, speaker_notes = _extract_pptx(file_bytes, include_notes)
    else:
        raise ValueError("Alleen .pdf en .pptx worden ondersteund.")

    raw_tokens_est = len(raw_full_text) // 4

    # 1. Afbeeldingen strippen
    pages = [_strip_images(page) for page in pages]
    # 2. Losse paginanummers verwijderen
    pages = [_strip_page_numbers(page) for page in pages]
    # 3. Herhaalde headers/footers verwijderen
    pages = _strip_repeated_headers(pages, repeat_threshold)
    # 4. Titelpagina samenvatten tot contextregel
    pages = _summarize_title_page(pages)
    # 5. Lege/triviale slides overslaan
    pages = _skip_trivial_pages(pages)
    # 6. Witruimte comprimeren
    clean_markdown = _compress_whitespace("\n\n".join(pages))
    clean_tokens_est = len(clean_markdown) // 4

    db.add(
        DocumentCache(
            file_hash=file_hash,
            filename=filename,
            clean_markdown=clean_markdown,
            speaker_notes=speaker_notes,
            raw_tokens_est=raw_tokens_est,
            clean_tokens_est=clean_tokens_est,
        )
    )
    metric = get_usage_metric(db)
    metric.tokens_saved_est = (metric.tokens_saved_est or 0) + max(
        0, raw_tokens_est - clean_tokens_est
    )
    db.commit()

    return {
        "clean_markdown": clean_markdown,
        "speaker_notes": speaker_notes,
        "raw_tokens_est": raw_tokens_est,
        "clean_tokens_est": clean_tokens_est,
        "cached": False,
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(
        description="Zet een PDF/PPTX lokaal om naar schone Markdown (0 tokens)."
    )
    parser.add_argument("file", help="Pad naar een .pdf- of .pptx-bestand")
    parser.add_argument(
        "--drempel",
        type=float,
        default=0.5,
        help="Drempel voor herhaalde headers/footers (standaard 0.5)",
    )
    parser.add_argument(
        "--notes",
        action="store_true",
        help="Laat sprekersnotities in de hoofdtekst staan",
    )
    args = parser.parse_args()

    # Late imports zodat de CLI ook werkt wanneer je modellen nog niet geladen zijn.
    from database import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)

    with open(args.file, "rb") as handle:
        file_bytes = handle.read()

    db = SessionLocal()
    try:
        result = process_file(
            file_bytes,
            os.path.basename(args.file),
            db,
            repeat_threshold=args.drempel,
            include_notes=args.notes,
        )
    except ValueError as exc:
        print(f"Fout: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    meta = {key: value for key, value in result.items() if key != "clean_markdown"}
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    print("\n--- Schone Markdown ---\n")
    print(result["clean_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
