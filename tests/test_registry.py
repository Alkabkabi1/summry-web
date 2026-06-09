"""Tests for subject registry and storage."""

from __future__ import annotations

import pytest

from pipeline.registry import (
    create_subject,
    get_subject,
    list_subjects,
    resolve_subject,
    slugify,
    study_pack_dir,
)


def test_slugify_normalizes_name():
    assert slugify("Operating Systems") == "operating-systems"
    assert slugify("  AI/ML 101 ") == "ai-ml-101"


def test_create_subject_writes_store_and_dirs(isolated_data):
    subject = create_subject("Database Systems", code="CS330", description="SQL and design")

    assert subject.slug == "database-systems"
    assert subject.code == "CS330"
    assert subject.name == "Database Systems"
    assert (isolated_data / "subjects" / "database-systems" / "pdfs").is_dir()
    assert (isolated_data / "subjects" / "database-systems" / "study-pack").is_dir()


def test_create_subject_is_idempotent(isolated_data):
    first = create_subject("Networking")
    second = create_subject("Networking")

    assert first.slug == second.slug
    assert len(list_subjects()) == 1


def test_resolve_subject_by_slug(isolated_data):
    created = create_subject("Ethics")
    resolved = resolve_subject(created.slug, None)

    assert resolved.slug == created.slug


def test_resolve_subject_creates_new(isolated_data):
    subject = resolve_subject(None, "New Course", new_subject_code="NC101")

    assert subject.slug == "new-course"
    assert subject.code == "NC101"


def test_resolve_subject_requires_input(isolated_data):
    with pytest.raises(ValueError, match="Select an existing subject"):
        resolve_subject(None, None)


def test_study_pack_dir_under_subject(isolated_data):
    subject = create_subject("OS")
    path = study_pack_dir(subject)

    assert path.name == "study-pack"
    assert subject.slug in str(path)


def test_get_subject_missing_returns_none(isolated_data):
    assert get_subject("does-not-exist") is None
