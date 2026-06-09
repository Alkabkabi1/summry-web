"""Extract plain text from uploaded PDF files."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

try:
    import fitz
except ImportError:
    fitz = None


def extract_pdf_text(pdf_path: Path) -> str:
    if fitz is not None:
        doc = fitz.open(pdf_path)
        try:
            return "\n".join(page.get_text() for page in doc)
        finally:
            doc.close()

    reader = PdfReader(str(pdf_path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def save_extracted_text(pdf_path: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    text = extract_pdf_text(pdf_path)
    if not text.strip():
        raise ValueError("Could not extract text from this PDF. It may be image-only or empty.")

    stem = pdf_path.stem.replace(" ", "_").replace("#", "")
    out_path = out_dir / f"{stem}.txt"
    out_path.write_text(text, encoding="utf-8")
    return out_path
