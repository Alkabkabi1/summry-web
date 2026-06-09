"""Integration tests for the full upload pipeline."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from pipeline.process import process_upload
from pipeline.registry import create_subject, get_subject, study_pack_dir


@pytest.fixture
def fake_pdf(tmp_path):
    path = tmp_path / "lecture.pdf"
    path.write_bytes(b"%PDF-1.4 fake")
    return path


def test_process_upload_creates_study_pack(isolated_data, fake_pdf, sample_lecture_text, tmp_path):
    extracted = tmp_path / "lecture.txt"
    extracted.write_text(sample_lecture_text, encoding="utf-8")

    subject = create_subject("Integration Test", code="INT101")

    with patch("pipeline.process.save_extracted_text", return_value=extracted):
        pack = process_upload(fake_pdf, subject, "lecture.pdf")

    assert pack.title
    assert pack.filename.endswith(".html")

    out = study_pack_dir(subject)
    assert (out / "index.html").exists()
    assert (out / pack.filename).exists()

    updated = get_subject(subject.slug)
    assert updated is not None
    assert len(updated.packs) == 1
