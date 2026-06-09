"""Subject registry — all data lives inside summry_web/data/."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import DATA_DIR, SUBJECTS_DIR, SUBJECTS_JSON


@dataclass
class PackInfo:
    id: str
    title: str
    filename: str
    pdf_name: str
    created_at: str


@dataclass
class SubjectInfo:
    slug: str
    name: str
    code: str = ""
    description: str = ""
    packs: list[PackInfo] = field(default_factory=list)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "subject"


def _store_path() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return SUBJECTS_JSON


def load_store() -> dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return {"subjects": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_store(data: dict[str, Any]) -> None:
    _store_path().write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def subject_dir(slug: str) -> Path:
    return SUBJECTS_DIR / slug


def study_pack_dir(subject: SubjectInfo) -> Path:
    return subject_dir(subject.slug) / "study-pack"


def lectures_json_path(subject: SubjectInfo) -> Path:
    return subject_dir(subject.slug) / "lectures.json"


def _parse_subject(raw: dict[str, Any]) -> SubjectInfo:
    packs = [PackInfo(**p) for p in raw.get("packs", [])]
    return SubjectInfo(
        slug=raw["slug"],
        name=raw["name"],
        code=raw.get("code", ""),
        description=raw.get("description", ""),
        packs=packs,
    )


def list_subjects() -> list[SubjectInfo]:
    store = load_store()
    return [_parse_subject(s) for s in store.get("subjects", [])]


def get_subject(slug: str) -> SubjectInfo | None:
    for subject in list_subjects():
        if subject.slug == slug:
            return subject
    return None


def create_subject(name: str, code: str = "", description: str = "") -> SubjectInfo:
    slug = slugify(name)
    store = load_store()
    subjects = store.setdefault("subjects", [])
    for s in subjects:
        if s["slug"] == slug:
            return _parse_subject(s)

    base_slug = slug
    n = 2
    while any(s["slug"] == slug for s in subjects):
        slug = f"{base_slug}-{n}"
        n += 1

    entry = {
        "slug": slug,
        "name": name.strip(),
        "code": code.strip(),
        "description": description.strip(),
        "packs": [],
    }
    subjects.append(entry)
    save_store(store)

    root = subject_dir(slug)
    (root / "pdfs").mkdir(parents=True, exist_ok=True)
    (root / "_extracted").mkdir(parents=True, exist_ok=True)
    (root / "study-pack").mkdir(parents=True, exist_ok=True)
    return _parse_subject(entry)


def resolve_subject(
    subject_slug: str | None,
    new_subject_name: str | None,
    new_subject_code: str = "",
    new_subject_description: str = "",
) -> SubjectInfo:
    if subject_slug:
        subject = get_subject(subject_slug)
        if subject:
            return subject
    if new_subject_name and new_subject_name.strip():
        return create_subject(
            new_subject_name.strip(),
            code=new_subject_code,
            description=new_subject_description,
        )
    raise ValueError("Select an existing subject or enter a new subject name.")


def add_pack_to_subject(subject: SubjectInfo, pack: PackInfo) -> None:
    store = load_store()
    for raw in store.get("subjects", []):
        if raw["slug"] != subject.slug:
            continue
        packs = raw.setdefault("packs", [])
        packs.append(asdict(pack))
        save_store(store)
        return


def next_pack_index(subject: SubjectInfo) -> int:
    return len(subject.packs) + 1
