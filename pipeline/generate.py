"""Generate HTML study packs from structured lecture content."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def slugify_filename(title: str, index: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    slug = slug[:48] or "lecture"
    return f"{index:02d}-{slug}.html"


def tag_badge(tag: str) -> str:
    cls = "tag-core" if tag.lower() == "core" else "tag-detail"
    return f'<span class="tag {cls}">[{esc(tag)}]</span>'


def render_scenarios(scenarios: list[dict]) -> str:
    parts = ["<h3>When to use X vs Y</h3>"]
    for s in scenarios:
        parts.append(
            f'<div class="scenario"><strong>{esc(s["title"])}</strong> '
            f"{esc(s['body'])}</div>"
        )
    return "\n".join(parts)


def render_definitions(defs: list[dict]) -> str:
    return '<div class="def-grid">' + "".join(
        f'<div class="def-item"><strong>{esc(d["term"])}:</strong> {esc(d["def"])}</div>'
        for d in defs
    ) + "</div>"


def render_flashcards(cards: list[dict]) -> str:
    items = []
    for c in cards:
        items.append(
            f'<div class="flashcard" tabindex="0">'
            f'<div class="flashcard-inner">'
            f'<div class="flashcard-front">{tag_badge(c["tag"])}<p>{esc(c["prompt"])}</p></div>'
            f'<div class="flashcard-back"><p><strong>Answer:</strong> {esc(c["answer"])}</p>'
            f'<p><em>Example:</em> {esc(c["example"])}</p></div></div></div>'
        )
    return '<div class="flashcard-grid">' + "".join(items) + "</div>"


def render_questions(questions: list[dict]) -> str:
    blocks = []
    for i, q in enumerate(questions, 1):
        qtype = q["type"]
        cls = "mcq" if qtype == "mc" else "tf"
        diff = q.get("difficulty", "Medium")
        body = f'<p class="mcq-num">Q{i} <span class="diff">[{esc(diff)}]</span></p>'
        body += f"<p>{esc(q['question'])}</p>"
        if qtype == "mc":
            body += "<ul>"
            for opt in q["options"]:
                body += f"<li>{esc(opt)}</li>"
            body += "</ul>"
        else:
            body += "<p><em>True or False</em></p>"
        ans = q["answer"]
        expl = q.get("explanation", "")
        blocks.append(
            f'<div class="{cls}">{body}'
            f'<div class="answer-key hidden"><span class="correct">Answer: {esc(ans)}</span>'
            f"<br>{esc(expl)}</div></div>"
        )
    return "\n".join(blocks)


def render_summary(lec: dict) -> str:
    tldr = "".join(f"<li>{esc(x)}</li>" for x in lec["tldr"])
    concepts = "".join(f"<li>{esc(x)}</li>" for x in lec["concepts"])
    testable = "".join(f"<li>{esc(x)}</li>" for x in lec["testable"])
    confusions = "".join(
        f'<div class="trap"><strong>Confusion:</strong> {esc(x)}</div>'
        for x in lec["confusions"]
    )
    return f"""
<section class="card" id="summary">
  <h2>Section A — Summary</h2>
  <h3>TL;DR</h3>
  <ul class="tldr">{tldr}</ul>
  {render_scenarios(lec["scenarios"])}
  <h3>Key concepts</h3>
  <ul class="concepts">{concepts}</ul>
  <h3>Definitions</h3>
  {render_definitions(lec["definitions"])}
  <h3>Top 10 testable</h3>
  <ol>{testable}</ol>
  <h3>Common confusions</h3>
  {confusions}
</section>"""


def render_page(lec: dict, brand_title: str, assets_prefix: str) -> str:
    title = lec["title"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} — {esc(brand_title)}</title>
  <link rel="stylesheet" href="{assets_prefix}/study-pack.css">
</head>
<body>
<div class="layout">
  <aside class="sidebar">
    <div class="sidebar-brand">
      <h1>{esc(brand_title)}</h1>
      <p>{esc(lec.get("subtitle", ""))}</p>
    </div>
    <nav>
      <ul class="nav-list">
        <li><a href="#summary">Summary</a></li>
        <li><a href="#scenarios">Scenarios</a></li>
        <li><a href="#flashcards">Flashcards</a></li>
        <li><a href="#test">Test</a></li>
        <li><a href="#answers">Answer Key</a></li>
      </ul>
    </nav>
  </aside>
  <main class="main">
    <a class="back-link" href="index.html">← All lectures</a>
    <header class="hero">
      <h2>{esc(title)}</h2>
      <p class="meta">{esc(lec.get("meta", ""))}</p>
    </header>
    {render_summary(lec)}
    <section class="card" id="scenarios">
      <h2>Section B — Scenarios</h2>
      {render_scenarios(lec.get("scenario_section", lec["scenarios"]))}
    </section>
    <section class="card" id="flashcards">
      <h2>Flashcards ({len(lec["flashcards"])})</h2>
      <p>Click a card to flip. Tags: [Core] exam-critical · [Detail] supporting depth.</p>
      {render_flashcards(lec["flashcards"])}
    </section>
    <section class="card" id="test">
      <h2>Section C — Practice Test</h2>
      <p>10 questions — mix of multiple choice and true/false.</p>
      {render_questions(lec["questions"])}
      <button type="button" class="reveal-answers">Show all answers</button>
    </section>
    <section class="card" id="answers">
      <h2>Answer Key</h2>
      <p>Use the button above or scroll each question block after revealing.</p>
      {render_questions(lec["questions"])}
    </section>
  </main>
</div>
<script src="{assets_prefix}/study-pack.js"></script>
</body>
</html>"""


def render_index(lectures: list[dict], subject_name: str, pack_count_label: str, assets_prefix: str) -> str:
    items = []
    for lec in lectures:
        items.append(
            f'<li><a href="{esc(lec["filename"])}">{esc(lec["title"])}</a>'
            f' <span class="tag tag-core">Exam prep</span></li>'
        )
    list_html = "\n        ".join(items)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(subject_name)} — Study Packs</title>
  <link rel="stylesheet" href="{assets_prefix}/study-pack.css">
  <style>
    .index-hero {{ text-align: center; padding: 2rem; }}
    .index-list {{ list-style: none; padding: 0; max-width: 640px; margin: 0 auto; }}
    .index-list li {{ margin: 0.75rem 0; padding: 1rem; background: var(--surface);
      border-radius: var(--radius); border: 1px solid var(--border); }}
    .index-list a {{ font-weight: 600; color: var(--primary); text-decoration: none; }}
    .badge-exam {{ background: #fef3c7; color: #92400e; }}
    .hub-back {{ display: inline-block; margin-bottom: 1rem; color: var(--primary); text-decoration: none; font-weight: 600; }}
  </style>
</head>
<body>
  <main class="main" style="max-width:720px;margin:0 auto;">
    <a class="hub-back" href="/">← Study Pack Hub</a>
    <header class="hero index-hero">
      <h2>{esc(subject_name)}</h2>
      <p class="meta">Study packs generated from uploaded PDFs</p>
      <p><span class="tag badge-exam">Exam prep</span> {esc(pack_count_label)}</p>
    </header>
    <section class="card">
      <h2>Lectures</h2>
      <ol class="index-list">
        {list_html}
      </ol>
    </section>
  </main>
  <script src="{assets_prefix}/study-pack.js"></script>
</body>
</html>"""


def write_study_pack(
    lectures: list[dict],
    out_dir: Path,
    brand_title: str,
    assets_src: Path,
    assets_url_prefix: str,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = out_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    for name in ("study-pack.css", "study-pack.js"):
        src = assets_src / name
        if src.exists():
            (assets_dir / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    for lec in lectures:
        path = out_dir / lec["filename"]
        path.write_text(
            render_page(lec, brand_title, f"{assets_url_prefix}/assets"),
            encoding="utf-8",
        )

    index_path = out_dir / "index.html"
    count_label = f"{len(lectures)} lecture{'s' if len(lectures) != 1 else ''}"
    index_path.write_text(
        render_index(lectures, brand_title, count_label, f"{assets_url_prefix}/assets"),
        encoding="utf-8",
    )


def load_lectures_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_lectures_json(path: Path, lectures: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lectures, indent=2, ensure_ascii=False), encoding="utf-8")


def append_lecture(
    lectures: list[dict],
    content: dict[str, Any],
    pack_index: int,
) -> dict[str, Any]:
    filename = slugify_filename(content["title"], pack_index)
    lec = {**content, "filename": filename}
    lectures.append(lec)
    return lec
