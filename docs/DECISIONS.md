# Decisions

## 2026-11-05 — Phase 1 baseline

- Keep the existing CareerCanvas visual identity and dependency-free browser frontend.
- Use a `src/` layout and FastAPI as the target API framework.
- Keep local, rule-based generation as the default so the project runs without credentials.
- Use only fictional data in examples and tests; runtime profiles and uploads stay under ignored `data/`.
- The existing prototype backend is temporarily relocated to `src/careercanvas/api.py`; its implementation will be replaced by the typed FastAPI API in Phase 2.
