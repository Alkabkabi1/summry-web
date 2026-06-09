# Summry Web

Standalone web app: upload a lecture PDF, pick or create a subject, and get a full **study pack** — summary, flashcards, scenarios, and a 10-question practice test.

**Repository:** [github.com/Alkabkabi1/summry-web](https://github.com/Alkabkabi1/summry-web)

Everything lives inside this project folder (no dependency on other repos).

---

## Quick start

```powershell
cd summry_web
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000/**

Or use the helper script:

```powershell
.\start.ps1
```

---

## Usage

1. **Hub** (`/`) — subject tabs on the left, upload form and pack list on the right.
2. **New subject** (`/subjects/new`) — create a subject before uploading (optional; you can also create one during upload).
3. **Upload PDF** — select subject or type a new name → **Generate study pack**.
4. **Open pack** — click a pack title to open the HTML study page (summary, flashcards, test).

After processing, the page refreshes and the new pack appears under that subject.

---

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | *(unset)* | Enables AI-generated summaries (richer packs) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model for summarization |
| `FLASK_SECRET_KEY` | dev default | Flask session/flash signing |
| `PORT` | `5000` | Server port |

**Basic mode** (no API key): summaries are built from extracted PDF text automatically.  
**AI mode** (with key): structured exam-prep content via OpenAI JSON output.

```powershell
$env:OPENAI_API_KEY = "sk-..."
python app.py
```

---

## Project structure

```
summry_web/
├── app.py                 # Flask routes
├── config.py              # paths and limits
├── pipeline/
│   ├── extract.py         # PDF → plain text
│   ├── summarize.py       # text → structured lecture dict
│   ├── generate.py        # lecture dict → HTML pages
│   ├── process.py         # orchestrates upload pipeline
│   └── registry.py        # subjects + JSON storage
├── templates/             # hub, new subject, help
├── static/                # hub UI + study-pack assets
├── data/
│   ├── subjects.json      # subject metadata
│   └── subjects/{slug}/   # pdfs, extracts, HTML output
├── tests/                 # pytest suite
├── requirements.txt
├── start.ps1
└── README.md
```

---

## Pipeline

```
PDF upload
    ↓
extract.py      →  _extracted/{name}.txt
    ↓
summarize.py    →  structured JSON (tldr, concepts, flashcards, questions, …)
    ↓
generate.py     →  study-pack/*.html + index.html
    ↓
registry.py     →  updates subjects.json + pack list in hub
```

Each study pack page includes:

| Section | Content |
|---------|---------|
| Summary | TL;DR, scenarios, concepts, definitions, testable points, confusions |
| Scenarios | “When to use X vs Y” |
| Flashcards | Click-to-flip, Core / Detail tags |
| Practice test | 10 MC + T/F questions |
| Answer key | Reveal all answers |

---

## Tests

Install dev dependencies (included in `requirements.txt`):

```powershell
cd summry_web
pip install -r requirements.txt
python -m pytest
```

You can also run from the **repo root** (`just chat/`):

```powershell
python -m pytest -v
```

Run with verbose output from inside `summry_web/`:

```powershell
python -m pytest -v
```

Run a single file:

```powershell
python -m pytest tests/test_registry.py
```

### Test coverage

| File | What it checks |
|------|----------------|
| `test_registry.py` | Subject create/slug/resolve, on-disk folders |
| `test_summarize.py` | Basic summarizer schema, flashcards, questions |
| `test_generate.py` | HTML output, file writes, JSON roundtrip |
| `test_extract.py` | PDF extraction edge cases |
| `test_process.py` | End-to-end upload pipeline (mocked extract) |
| `test_app.py` | Flask routes, upload validation, redirects |

Tests use a **temporary data directory** (via `conftest.py`) so your real uploads in `data/` are never touched.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| “Could not extract text from this PDF” | PDF may be image-only; try OCR source or a text-based PDF |
| Processing is slow | Large PDFs + OpenAI calls take time; wait for the overlay to finish |
| Port already in use | `$env:PORT = "5001"; python app.py` |
| Rich summaries not appearing | Set `OPENAI_API_KEY` and restart the server |

---

## Data storage

All user data stays under `data/subjects/{slug}/`:

```
data/subjects/database-systems/
├── pdfs/              uploaded PDFs
├── _extracted/        plain-text extracts
├── lectures.json      structured content (source of truth)
└── study-pack/        generated HTML + assets
    ├── index.html
    ├── 01-lecture.html
    └── assets/
```

To reset everything, delete `data/subjects/` and reset `data/subjects.json` to `{"subjects": []}`.
