"""Tests for HTML study-pack generation."""

from __future__ import annotations

from pathlib import Path

from pipeline.generate import (
    append_lecture,
    load_lectures_json,
    render_page,
    save_lectures_json,
    slugify_filename,
    write_study_pack,
)


def _minimal_lecture() -> dict:
    return {
        "title": "Test Lecture",
        "subtitle": "Unit 1",
        "meta": "Test meta",
        "tldr": ["Point one about software products."],
        "concepts": ["Generic software products serve many customers."],
        "definitions": [{"term": "Product", "def": "Generic software for many customers."}],
        "testable": ["Define software product."],
        "confusions": ["Custom vs product engineering differ on who owns requirements."],
        "scenarios": [{"title": "Custom vs product", "body": "Use custom when client owns requirements."}],
        "scenario_section": [{"title": "Hybrid vs SaaS", "body": "Hybrid keeps partial local execution."}],
        "flashcards": [
            {
                "tag": "Core",
                "prompt": "What is a software product?",
                "answer": "Generic functionality for many customers.",
                "example": "Excel, mobile apps.",
            }
        ],
        "questions": [
            {
                "type": "mc",
                "question": "Who decides features in product engineering?",
                "options": ["Client", "Developer", "Regulator", "Users"],
                "answer": "Developer",
                "explanation": "Product developer decides scope.",
                "difficulty": "Easy",
            }
        ],
    }


def test_slugify_filename_includes_index():
    assert slugify_filename("Hello World", 3) == "03-hello_world.html"


def test_render_page_contains_sections():
    html = render_page(_minimal_lecture(), "CS101", "/static/assets")

    assert "Section A — Summary" in html
    assert "Section B — Scenarios" in html
    assert "Flashcards" in html
    assert "Practice Test" in html
    assert "Test Lecture" in html


def test_write_study_pack_creates_files(tmp_path):
    assets = Path(__file__).resolve().parents[1] / "static" / "assets"
    lectures = [append_lecture([], _minimal_lecture(), 1)]
    out = tmp_path / "study-pack"

    write_study_pack(lectures, out, "CS101", assets, "/subjects/test/study-pack")

    assert (out / "index.html").exists()
    assert (out / lectures[0]["filename"]).exists()
    assert (out / "assets" / "study-pack.css").exists()
    assert (out / "assets" / "study-pack.js").exists()


def test_lectures_json_roundtrip(tmp_path):
    path = tmp_path / "lectures.json"
    data = [append_lecture([], _minimal_lecture(), 1)]

    save_lectures_json(path, data)
    loaded = load_lectures_json(path)

    assert loaded[0]["title"] == "Test Lecture"
    assert loaded[0]["filename"].endswith(".html")
