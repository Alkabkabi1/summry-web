"""Tests for lecture summarization (basic mode)."""

from __future__ import annotations

from pipeline.summarize import summarize_basic, summarize_text


REQUIRED_KEYS = {
    "title",
    "subtitle",
    "meta",
    "tldr",
    "concepts",
    "definitions",
    "testable",
    "confusions",
    "scenarios",
    "scenario_section",
    "flashcards",
    "questions",
    "pdf_source",
}


def test_summarize_basic_returns_full_schema(sample_lecture_text):
    result = summarize_basic(sample_lecture_text, "lecture1.pdf", "Software Engineering")

    assert REQUIRED_KEYS.issubset(result.keys())
    assert len(result["tldr"]) >= 1
    assert len(result["concepts"]) >= 1
    assert len(result["flashcards"]) >= 1
    assert len(result["questions"]) == 10


def test_summarize_basic_flashcard_tags(sample_lecture_text):
    result = summarize_basic(sample_lecture_text, "lecture1.pdf", "SE")

    tags = {c["tag"] for c in result["flashcards"]}
    assert tags.issubset({"Core", "Detail"})


def test_summarize_basic_questions_have_types(sample_lecture_text):
    result = summarize_basic(sample_lecture_text, "lecture1.pdf", "SE")

    for q in result["questions"]:
        assert q["type"] in ("mc", "tf")
        assert q["answer"]
        if q["type"] == "mc":
            assert len(q["options"]) == 4


def test_summarize_text_falls_back_without_api_key(sample_lecture_text, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = summarize_text(sample_lecture_text, "lecture1.pdf", "SE")

    assert "basic mode" in result["meta"].lower() or "Generated from" in result["meta"]
