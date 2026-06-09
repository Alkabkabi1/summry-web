"""Flask route and upload validation tests."""

from __future__ import annotations

import io
from unittest.mock import patch

import pytest

from app import app
from pipeline.registry import PackInfo


@pytest.fixture
def client(isolated_data):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_hub_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Summry Web" in response.data


def test_help_returns_200(client):
    response = client.get("/help")
    assert response.status_code == 200
    assert b"How it works" in response.data


def test_new_subject_get(client):
    response = client.get("/subjects/new")
    assert response.status_code == 200
    assert b"Create subject" in response.data


def test_new_subject_post_creates_subject(client):
    response = client.post(
        "/subjects/new",
        data={"name": "Test Subject", "code": "TS101", "description": "For tests"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Test Subject" in response.data


def test_upload_rejects_missing_file(client):
    response = client.post("/upload", data={}, follow_redirects=True)

    assert response.status_code == 200
    assert b"choose a pdf" in response.data.lower()


def test_upload_rejects_non_pdf(client):
    response = client.post(
        "/upload",
        data={
            "new_subject_name": "Bad Upload",
            "pdf": (io.BytesIO(b"not a pdf"), "notes.txt"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Only PDF" in response.data


def test_upload_success_redirects(client, isolated_data):
    fake_pack = PackInfo(
        id="abc123",
        title="Mock Lecture",
        filename="01-mock_lecture.html",
        pdf_name="lecture.pdf",
        created_at="2026-01-01T00:00:00+00:00",
    )

    with patch("app.process_upload", return_value=fake_pack):
        response = client.post(
            "/upload",
            data={
                "new_subject_name": "Upload Course",
                "pdf": (io.BytesIO(b"%PDF-1.4"), "lecture.pdf"),
            },
            content_type="multipart/form-data",
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert b"Mock Lecture" in response.data


def test_study_pack_404_for_unknown_subject(client):
    response = client.get("/subjects/unknown-slug/study-pack/index.html")
    assert response.status_code == 404
