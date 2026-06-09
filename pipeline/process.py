"""End-to-end PDF → study pack pipeline."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from config import APP_ROOT
from pipeline.extract import save_extracted_text
from pipeline.generate import (
    append_lecture,
    load_lectures_json,
    save_lectures_json,
    write_study_pack,
)
from pipeline.registry import (
    PackInfo,
    SubjectInfo,
    _now,
    add_pack_to_subject,
    lectures_json_path,
    next_pack_index,
    study_pack_dir,
)
from pipeline.summarize import summarize_text

ASSETS_SRC = APP_ROOT / "static" / "assets"


def process_upload(pdf_path: Path, subject: SubjectInfo, original_name: str) -> PackInfo:
    root = study_pack_dir(subject).parent
    pdfs_dir = root / "pdfs"
    extracted_dir = root / "_extracted"
    pdfs_dir.mkdir(parents=True, exist_ok=True)

    safe_name = original_name.replace("..", "").replace("/", "_").replace("\\", "_")
    stored_pdf = pdfs_dir / safe_name
    shutil.copy2(pdf_path, stored_pdf)

    txt_path = save_extracted_text(stored_pdf, extracted_dir)
    text = txt_path.read_text(encoding="utf-8")

    brand = subject.name if not subject.code else f"{subject.code} — {subject.name}"
    content = summarize_text(text, safe_name, brand)
    content["meta"] = content.get("meta") or f"Generated from {safe_name}"

    lectures_path = lectures_json_path(subject)
    lectures = load_lectures_json(lectures_path)
    pack_index = next_pack_index(subject)
    lec = append_lecture(lectures, content, pack_index)
    save_lectures_json(lectures_path, lectures)

    out_dir = study_pack_dir(subject)
    assets_url = f"/subjects/{subject.slug}/study-pack"
    write_study_pack(lectures, out_dir, brand, ASSETS_SRC, assets_url)

    pack = PackInfo(
        id=str(uuid.uuid4())[:8],
        title=lec["title"],
        filename=lec["filename"],
        pdf_name=safe_name,
        created_at=_now(),
    )
    add_pack_to_subject(subject, pack)
    return pack
