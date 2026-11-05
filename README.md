# CareerCanvas

> Local-first, AI-assisted career content generation for students.

CareerCanvas turns a student's skills, academic interests, career goals, project evidence, and optional resume into a professional summary, computed skill-gap report, learning plan, and interview preparation pack. Every format is rendered from one canonical career report so the UI, JSON, Markdown, DOCX, and PDF cannot drift apart.

## Status

Phase 1 repository restructuring is complete. Domain models, deterministic analysis, provider integrations, exporters, and the full test/CI quality gate are being added in subsequent phases.

## Quick start

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
make run
```

Open `http://127.0.0.1:8000`. The default mode is offline and requires no API key.

## Repository layout

- `src/careercanvas/` — typed application package
- `static/` — dependency-free CareerCanvas frontend
- `examples/` — fictional demo profiles only
- `data/` — ignored local profiles, uploads, and role data
- `tests/` — automated quality gates
- `docs/` — architecture and project decisions

## Privacy

Local profile data and uploads are ignored by Git and remain on the local machine by default. External LLM providers are opt-in and will be documented before that integration is enabled.

## Responsible use

Generated career content is guidance, not a guarantee. Review every claim before using it, and never present generated text as experience or achievement you did not earn.

