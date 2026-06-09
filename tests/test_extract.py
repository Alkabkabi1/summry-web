"""Tests for PDF text extraction."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfWriter

from pipeline.extract import extract_pdf_text, save_extracted_text


def _blank_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with path.open("wb") as f:
        writer.write(f)


def test_save_extracted_text_rejects_empty_pdf(tmp_path):
    pdf = tmp_path / "empty.pdf"
    _blank_pdf(pdf)

    with pytest.raises(ValueError, match="Could not extract text"):
        save_extracted_text(pdf, tmp_path / "out")


def test_extract_pdf_text_returns_string(tmp_path):
    pdf = tmp_path / "blank.pdf"
    _blank_pdf(pdf)

    text = extract_pdf_text(pdf)

    assert isinstance(text, str)
