"""FastAPI application entry point for CareerCanvas.

The typed domain and generation pipeline are introduced in later phases.
"""

import base64
import binascii
import json
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse

from .config import settings

ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = ROOT / "static"
EXAMPLE_PROFILE = ROOT / "examples" / "sample_profile.json"
UPLOAD_DIR = ROOT / "data" / "uploads"
MAX_UPLOAD_BYTES = 6 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".zip",
    ".png",
    ".jpg",
    ".jpeg",
}

app = FastAPI(title="CareerCanvas", version="0.1.0")


def demo_state(profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a frontend-compatible demo state during the Phase 1 migration."""

    if profile is None:
        profile = json.loads(EXAMPLE_PROFILE.read_text(encoding="utf-8"))
    skills = profile.get("skills", [])
    role = profile.get("target_role", "Career explorer")
    questions = [
        f"Tell me about a project where you used {skills[0] if skills else 'your strongest skill'}.",
        "How did feedback change one of your decisions?",
        "What would you improve if you had another week?",
    ]
    return {
        "profile": profile,
        "report": {
            "headline": f"{role} with a systems mindset.",
            "score": 72,
            "professional_summary": (
                f"{profile['name']} is an aspiring {role.lower()} who combines "
                f"{', '.join(skills[:3])} with curiosity and practical project experience."
            ),
            "summary": (
                f"{profile['name']} is an aspiring {role.lower()} who combines "
                f"{', '.join(skills[:3])} with curiosity and practical project experience."
            ),
            "strengths": skills[:3],
            "skill_gap_report": [],
            "learning_recommendations": [],
            "interview_preparation": {"pitch": "", "questions": questions},
            "evidence_files": [],
        },
    }


@app.get("/api/health")
def health() -> dict[str, bool | str]:
    """Return a lightweight service health response."""

    return {"ok": True, "service": "careercanvas"}


@app.get("/api/profile")
def get_profile() -> dict[str, Any]:
    """Return the temporary demo state used by the migrated frontend."""

    return demo_state()


@app.post("/api/profile")
async def update_profile(request: Request) -> dict[str, Any]:
    """Return a regenerated demo state for the migrated profile form."""

    payload = await request.json()
    profile = json.loads(EXAMPLE_PROFILE.read_text(encoding="utf-8"))
    profile.update({key: value for key, value in payload.items() if key in profile})
    if isinstance(profile.get("skills"), str):
        profile["skills"] = [item.strip() for item in profile["skills"].split(",") if item.strip()]
    return demo_state(profile)


@app.post("/api/uploads")
async def upload_evidence(request: Request) -> dict[str, Any]:
    """Accept the current frontend's base64 upload payload.

    Full resume extraction is introduced with the Phase 6 parser. This endpoint
    persists the evidence locally now so the UI does not fail during migration.
    """

    payload = await request.json()
    name = Path(str(payload.get("name", ""))).name
    encoded = payload.get("content", "")
    extension = Path(name).suffix.lower()
    if not name or extension not in ALLOWED_EXTENSIONS or not isinstance(encoded, str):
        raise HTTPException(status_code=400, detail="Unsupported or invalid upload.")
    try:
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as error:
        raise HTTPException(
            status_code=400, detail="Upload content is not valid base64."
        ) from error
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Upload exceeds the 6 MB limit.")
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "-", name).strip(".-")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / safe_name).write_bytes(content)
    profile_state = demo_state()
    profile_state["report"]["evidence_files"] = [{"name": safe_name, "size": len(content)}]
    return profile_state


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the allow-listed frontend entry point."""

    return FileResponse(STATIC_DIR / "index.html")


@app.get("/{asset_path:path}", include_in_schema=False)
def static_asset(asset_path: str) -> FileResponse:
    """Serve only known static assets, never arbitrary project files."""

    allowed = {"index.html", "script.js", "styles.css"}
    if asset_path not in allowed:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(STATIC_DIR / asset_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("careercanvas.api:app", host=settings.host, port=settings.port)
