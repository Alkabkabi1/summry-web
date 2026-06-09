"""Shared pytest fixtures — isolated data dir so tests never touch real uploads."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def sample_lecture_text() -> str:
    return (FIXTURES / "sample_lecture.txt").read_text(encoding="utf-8")


@pytest.fixture
def isolated_data(tmp_path, monkeypatch):
    data = tmp_path / "data"
    subjects = data / "subjects"
    subjects.mkdir(parents=True)
    subjects_json = data / "subjects.json"
    subjects_json.write_text(json.dumps({"subjects": []}), encoding="utf-8")

    for module in ("config", "pipeline.registry"):
        monkeypatch.setattr(f"{module}.DATA_DIR", data)
        monkeypatch.setattr(f"{module}.SUBJECTS_DIR", subjects)
        monkeypatch.setattr(f"{module}.SUBJECTS_JSON", subjects_json)

    return data
