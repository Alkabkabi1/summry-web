#!/usr/bin/env python3
"""Summry Web — standalone PDF → study pack app (lives entirely in summry_web/)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

from config import ALLOWED_EXTENSIONS, APP_ROOT, MAX_UPLOAD_MB
from pipeline.process import process_upload
from pipeline.registry import create_subject, get_subject, list_subjects, resolve_subject, study_pack_dir

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "summry-web-dev-key")


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.route("/")
def hub():
    active_slug = request.args.get("subject") or ""
    subjects = list_subjects()
    if not active_slug and subjects:
        active_slug = subjects[0].slug
    active = get_subject(active_slug) if active_slug else None
    return render_template(
        "hub.html",
        subjects=subjects,
        active=active,
        active_slug=active_slug,
        openai_configured=bool(os.environ.get("OPENAI_API_KEY")),
    )


@app.route("/help")
def help_page():
    return render_template(
        "help.html",
        openai_configured=bool(os.environ.get("OPENAI_API_KEY")),
    )


@app.route("/subjects/new", methods=["GET", "POST"])
def new_subject():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip()
        description = request.form.get("description", "").strip()
        if not name:
            flash("Subject name is required.", "error")
            return render_template("new_subject.html")
        subject = create_subject(name, code=code, description=description)
        flash(f"Subject created: {subject.name}", "success")
        return redirect(url_for("hub", subject=subject.slug))
    return render_template("new_subject.html")


@app.route("/upload", methods=["POST"])
def upload():
    pdf = request.files.get("pdf")
    subject_slug = request.form.get("subject_slug", "").strip()
    new_subject_name = request.form.get("new_subject_name", "").strip()
    new_subject_code = request.form.get("new_subject_code", "").strip()
    new_subject_description = request.form.get("new_subject_description", "").strip()

    if not pdf or not pdf.filename:
        flash("Please choose a PDF file to upload.", "error")
        return redirect(url_for("hub", subject=subject_slug or None))

    if not allowed_file(pdf.filename):
        flash("Only PDF files are supported.", "error")
        return redirect(url_for("hub", subject=subject_slug or None))

    pdf.stream.seek(0, os.SEEK_END)
    size_mb = pdf.stream.tell() / (1024 * 1024)
    pdf.stream.seek(0)
    if size_mb > MAX_UPLOAD_MB:
        flash(f"File is too large (max {MAX_UPLOAD_MB} MB).", "error")
        return redirect(url_for("hub", subject=subject_slug or None))

    try:
        subject = resolve_subject(
            subject_slug or None,
            new_subject_name or None,
            new_subject_code=new_subject_code,
            new_subject_description=new_subject_description,
        )
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("hub"))

    original_name = secure_filename(pdf.filename) or "upload.pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.save(tmp.name)
        tmp_path = Path(tmp.name)

    try:
        pack = process_upload(tmp_path, subject, original_name)
        flash(f"Study pack created: {pack.title}", "success")
        return redirect(url_for("hub", subject=subject.slug, _anchor="packs"))
    except Exception as exc:
        flash(f"Processing failed: {exc}", "error")
        return redirect(url_for("hub", subject=subject.slug))
    finally:
        tmp_path.unlink(missing_ok=True)


@app.route("/subjects/<slug>/study-pack/<path:filename>")
def serve_study_pack(slug: str, filename: str):
    subject = get_subject(slug)
    if not subject:
        return "Subject not found", 404
    return send_from_directory(study_pack_dir(subject), filename)


@app.route("/static/<path:filename>")
def serve_static(filename: str):
    return send_from_directory(APP_ROOT / "static", filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
