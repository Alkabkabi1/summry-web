"""Turn extracted lecture text into structured study-pack content."""

from __future__ import annotations

import json
import os
import re
from typing import Any

SUMMARY_SCHEMA_HINT = """
Return a JSON object with these keys:
- title: short lecture title inferred from content
- subtitle: optional chapter/lecture label
- meta: one-line source note
- tldr: array of 5 bullet strings
- concepts: array of 15-25 key concept strings
- definitions: array of {term, def} objects (6-10 items)
- testable: array of 10 exam-style prompt strings
- confusions: array of 3-7 common mistake strings
- scenarios: array of 3 {title, body} when-to-use-X-vs-Y items
- scenario_section: array of 2-3 extra {title, body} scenarios
- flashcards: array of 20-30 {tag, prompt, answer, example} where tag is Core or Detail
- questions: array of 10 {type, question, options?, answer, explanation, difficulty}
  type is "mc" (with 4 options) or "tf"
"""


def _clean_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if len(line) < 20:
            continue
        if re.fullmatch(r"\d+", line):
            continue
        lines.append(line)
    return lines


def _chunk_sentences(lines: list[str], limit: int) -> list[str]:
    joined = " ".join(lines)
    parts = re.split(r"(?<=[.!?])\s+", joined)
    out: list[str] = []
    for part in parts:
        part = part.strip()
        if len(part) >= 40:
            out.append(part)
        if len(out) >= limit:
            break
    return out


def _guess_title(lines: list[str], pdf_name: str) -> str:
    for line in lines[:12]:
        if len(line) <= 120 and not line.endswith("."):
            return line
    stem = re.sub(r"[_\-]+", " ", pdf_name)
    return stem.title()


def summarize_with_openai(text: str, pdf_name: str, subject_name: str) -> dict[str, Any]:
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)
    trimmed = text[:120_000]
    prompt = (
        f"You are building an exam-prep study pack for the subject '{subject_name}' "
        f"from source material '{pdf_name}'.\n"
        f"{SUMMARY_SCHEMA_HINT}\n"
        "Be accurate to the source. Use advanced exam-prep depth.\n\n"
        f"SOURCE TEXT:\n{trimmed}"
    )

    response = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You produce rigorous study-pack JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    content = response.choices[0].message.content or "{}"
    data = json.loads(content)
    return _normalize_lecture(data, pdf_name, subject_name)


def summarize_basic(text: str, pdf_name: str, subject_name: str) -> dict[str, Any]:
    lines = _clean_lines(text)
    sentences = _chunk_sentences(lines, 40)
    title = _guess_title(lines, pdf_name)

    tldr = sentences[:5] or [f"Summary of {title}."]
    concepts = sentences[:22] or tldr * 3
    definitions = []
    for sent in sentences[:12]:
        m = re.match(r"^([A-Z][A-Za-z0-9 \-/]{2,40})(?: is |: | — | - )(.+)$", sent)
        if m:
            definitions.append({"term": m.group(1).strip(), "def": m.group(2).strip()[:280]})
        if len(definitions) >= 8:
            break
    if not definitions:
        definitions = [
            {"term": title, "def": tldr[0][:280]},
            {"term": "Key theme", "def": (concepts[1] if len(concepts) > 1 else tldr[0])[:280]},
        ]

    testable = [f"Explain: {concepts[i][:100]}" for i in range(min(10, len(concepts)))]
    confusions = [
        "Do not confuse terminology that appears in similar contexts — check definitions.",
        "Slide titles may not match exam wording; focus on concepts from the summary.",
        "Image-only slides may omit details; verify against the full extracted text.",
    ]

    scenarios = [
        {
            "title": "Concept A vs Concept B",
            "body": "Use the definition that matches the problem context described in the source slides.",
        },
        {
            "title": "Theory vs application",
            "body": "Apply definitions when questions ask for examples; use theory when asked for principles.",
        },
    ]

    flashcards = []
    for i, concept in enumerate(concepts[:25], 1):
        tag = "Core" if i <= 12 else "Detail"
        flashcards.append(
            {
                "tag": tag,
                "prompt": f"What is important about: {concept[:90]}?",
                "answer": concept[:220],
                "example": "From uploaded PDF extract.",
            }
        )

    questions = []
    for i in range(10):
        concept = concepts[i % len(concepts)]
        if i % 2 == 0:
            questions.append(
                {
                    "type": "mc",
                    "question": f"Which statement best reflects the source material on '{concept[:70]}'?",
                    "options": [
                        concept[:120],
                        "Unrelated statement not supported by the PDF.",
                        "Opposite of the source material.",
                        "Generic statement with no source support.",
                    ],
                    "answer": concept[:120],
                    "explanation": "Derived from extracted PDF text (basic mode).",
                    "difficulty": "Medium",
                }
            )
        else:
            questions.append(
                {
                    "type": "tf",
                    "question": concept[:180],
                    "answer": "True",
                    "explanation": "Statement taken from extracted source text.",
                    "difficulty": "Easy",
                }
            )

    data = {
        "title": title,
        "subtitle": subject_name,
        "meta": f"Auto-generated from {pdf_name} (basic mode — set OPENAI_API_KEY for richer packs)",
        "tldr": tldr,
        "concepts": concepts,
        "definitions": definitions,
        "testable": testable,
        "confusions": confusions,
        "scenarios": scenarios,
        "scenario_section": scenarios[:2],
        "flashcards": flashcards,
        "questions": questions,
    }
    return _normalize_lecture(data, pdf_name, subject_name)


def summarize_text(text: str, pdf_name: str, subject_name: str) -> dict[str, Any]:
    if os.environ.get("OPENAI_API_KEY"):
        try:
            return summarize_with_openai(text, pdf_name, subject_name)
        except Exception:
            pass
    return summarize_basic(text, pdf_name, subject_name)


def _normalize_lecture(data: dict[str, Any], pdf_name: str, subject_name: str) -> dict[str, Any]:
    data.setdefault("title", _guess_title(_clean_lines(data.get("_text", "")), pdf_name))
    data.setdefault("subtitle", subject_name)
    data.setdefault("meta", f"Generated from {pdf_name}")
    data.setdefault("tldr", [])
    data.setdefault("concepts", [])
    data.setdefault("definitions", [])
    data.setdefault("testable", [])
    data.setdefault("confusions", [])
    data.setdefault("scenarios", [])
    data.setdefault("scenario_section", data.get("scenarios", []))
    data.setdefault("flashcards", [])
    data.setdefault("questions", [])
    data["pdf_source"] = pdf_name
    return data
