# CareerCanvas

> Local-first, AI-assisted career content generation for students.

CareerCanvas turns a student's skills, academic interests, career goals, project evidence, and optional resume into a professional summary, computed skill-gap report, learning plan, and interview preparation pack. Every format is rendered from one canonical career report so the UI, JSON, Markdown, DOCX, and PDF cannot drift apart.

## Status

CareerCanvas currently includes a working local profile API, evidence upload flow, and animated resume intelligence panel. Uploading a text-based PDF, DOCX, TXT, Markdown, CSV, or JSON file extracts text locally, detects resume sections, finds common skills with word-boundary matching, identifies contact signals, calculates a completeness score, and merges detected skills into the profile. Scanned/image-only documents are identified clearly as requiring OCR.

## Quick start

### Windows PowerShell

If `.venv` already exists, activate it instead of creating it again:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m uvicorn careercanvas.api:app --host 127.0.0.1 --port 8000 --reload
```

If you need a fresh environment, stop the server, deactivate the current environment,
and recreate it:

```powershell
deactivate
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m uvicorn careercanvas.api:app --host 127.0.0.1 --port 8000 --reload
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m uvicorn careercanvas.api:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000`. The default mode is offline and requires no API key.

### Make commands

The repository includes a `Makefile` for macOS/Linux and environments where GNU Make
is installed:

```bash
make install
make run
make test
make lint
make typecheck
```

GNU Make is not included with standard Windows PowerShell. On Windows, use the direct
Python commands above or run the Makefile through WSL/Git Bash with GNU Make installed.

## Repository layout

- `src/careercanvas/` — typed application package
- `static/` — dependency-free CareerCanvas frontend
- `examples/` — fictional demo profiles only
- `data/` — ignored local profiles, uploads, and role data
- `tests/` — automated quality gates
- `docs/` — architecture and project decisions

## Privacy

Local profile data and uploads are ignored by Git and remain on the local machine by default. External LLM providers are opt-in and will be documented before that integration is enabled.

## Evidence analysis

The upload workflow is an analysis step, not a file attachment placeholder:

1. The browser sends the selected file to `POST /api/uploads`.
2. The API decodes and stores it in the ignored local `data/uploads/` directory.
3. PDF text is extracted with `pypdf`; DOCX paragraphs and tables are extracted with `python-docx`; plain-text formats are decoded directly.
4. The analyzer detects sections, skills, email/phone signals, word count, and a 0–100 completeness score.
5. Detected skills are merged into the profile and all generated content is refreshed.

Image-only PDFs and images are stored safely but do not claim to have been analyzed. OCR is a planned upgrade.

## Responsible use

Generated career content is guidance, not a guarantee. Review every claim before using it, and never present generated text as experience or achievement you did not earn.
