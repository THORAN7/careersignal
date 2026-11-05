"""FastAPI application for the local-first CareerSignal workspace."""

import base64
import binascii
import json
import re
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from threading import Lock
from typing import Any, cast

from docx import Document
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .analysis.report import build_report
from .config import settings
from .consistency import check_report
from .exporters.render import to_docx, to_json, to_markdown, to_pdf

ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = ROOT / "static"
EXAMPLE_PROFILE = ROOT / "examples" / "sample_profile.json"
DATA_DIR = ROOT / "data"
PROFILE_FILE = DATA_DIR / "profile.json"
UPLOAD_DIR = DATA_DIR / "uploads"
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
DATA_LOCK = Lock()

app = FastAPI(title="CareerSignal", version="0.2.0")

EMPTY_PROFILE: dict[str, Any] = {
    "name": "",
    "degree": "",
    "year": "",
    "school": "",
    "skills": [],
    "interests": "",
    "goals": "",
    "experience": "",
    "target_role": "",
    "learning_completed": [False, False, False],
    "uploads": [],
    "updated_at": None,
    "resume_analysis": None,
}


def now() -> str:
    return datetime.now(UTC).isoformat()


def clean(value: Any, fallback: str = "") -> str:
    return str(value or fallback).strip()


def load_profile() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PROFILE_FILE.exists():
        PROFILE_FILE.write_text(json.dumps(EMPTY_PROFILE, indent=2), encoding="utf-8")
    try:
        profile = cast(dict[str, Any], json.loads(PROFILE_FILE.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=500, detail="Saved profile could not be read.") from error
    for key, value in EMPTY_PROFILE.items():
        profile.setdefault(key, value)
    return profile


def save_profile(profile: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary = PROFILE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    temporary.replace(PROFILE_FILE)


def extract_text(name: str, content: bytes) -> str:
    extension = Path(name).suffix.lower()
    if extension in {".txt", ".md", ".csv", ".json"}:
        return content.decode("utf-8", errors="ignore")
    if extension == ".docx":
        try:
            document = Document(BytesIO(content))
            paragraphs = [paragraph.text for paragraph in document.paragraphs]
            tables = [
                " ".join(cell.text for cell in row.cells)
                for table in document.tables
                for row in table.rows
            ]
            return "\n".join(paragraphs + tables)
        except (OSError, ValueError, KeyError, TypeError):
            return ""
    if extension == ".pdf":
        try:
            reader = PdfReader(BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except (OSError, ValueError, PdfReadError):
            return ""
    return ""


def analyse_evidence(name: str, content: bytes) -> dict[str, Any]:
    text = extract_text(name, content)
    sections = [
        section
        for section in (
            "education",
            "experience",
            "projects",
            "skills",
            "certifications",
            "summary",
        )
        if re.search(rf"\b{section}\b", text, re.IGNORECASE)
    ]
    skill_aliases = {
        "Python": ("python",),
        "SQL": (r"\bsql\b",),
        "JavaScript": ("javascript", "js", "ecmascript"),
        "Java": (r"\bjava\b",),
        "TypeScript": ("typescript", "ts"),
        "React": ("react", "react.js"),
        "Figma": ("figma",),
        "Research": ("user research", "research"),
        "Leadership": ("leadership", "led", "team lead"),
        "Communication": ("communication", "presented", "stakeholder"),
        "Data analysis": ("data analysis", "analytics", "pandas", "power bi", "tableau"),
        "Machine learning": ("machine learning", "tensorflow", "pytorch", "scikit-learn"),
        "Git": (r"\bgit\b", "github"),
    }
    detected = [
        skill
        for skill, aliases in skill_aliases.items()
        if any(re.search(rf"\b{re.escape(alias)}\b", text, re.IGNORECASE) for alias in aliases)
    ]
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone = re.search(r"(?:\+?\d[\d\s().-]{8,}\d)", text)
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    inferred_name = (
        first_line if first_line and "@" not in first_line and len(first_line.split()) <= 5 else ""
    )
    word_count = len(re.findall(r"\b[\w'-]+\b", text))
    status = "extracted" if word_count >= 8 else "stored"
    if Path(name).suffix.lower() in {".pdf", ".docx"} and not text:
        message = "No selectable text found. This may be a scanned document; use a text-based PDF or DOCX."
    elif text:
        message = f"Extracted {word_count} words and evaluated {len(detected)} skill signals across {len(sections)} sections."
    else:
        message = "File stored locally. Add text to a TXT, MD, CSV or JSON file for analysis."
    return {
        "status": status,
        "message": message,
        "completeness_score": min(
            100,
            20
            + min(35, word_count // 8)
            + len(sections) * 7
            + len(detected) * 4
            + (12 if email else 0)
            + (5 if phone else 0),
        ),
        "detected_skills": detected,
        "sections": sections,
        "contact": {
            "email": email.group(0) if email else "",
            "phone": phone.group(0) if phone else "",
        },
        "text_preview": text[:900],
        "word_count": word_count,
        "inferred_name": inferred_name,
    }


def report_for(profile: dict[str, Any]) -> dict[str, Any]:
    report = build_report(profile)
    report.consistency_warnings = check_report(report)
    return report.model_dump(mode="json")


def state() -> dict[str, Any]:
    profile = load_profile()
    return {"profile": profile, "report": report_for(profile)}


def demo_state(profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """Compatibility helper used by existing smoke tests."""
    return {"profile": profile or load_profile(), "report": report_for(profile or load_profile())}


@app.get("/api/health")
def health() -> dict[str, bool | str]:
    return {"ok": True, "service": "careersignal", "storage": str(PROFILE_FILE)}


@app.get("/api/profile")
def get_profile() -> dict[str, Any]:
    with DATA_LOCK:
        return state()


@app.get("/api/report/{format_name}")
def export_report(format_name: str) -> Response:
    """Export the same canonical report used by the dashboard."""
    report = build_report(load_profile())
    report.consistency_warnings = check_report(report)
    if format_name == "json":
        return JSONResponse(content=json.loads(to_json(report)))
    if format_name == "markdown":
        return Response(to_markdown(report), media_type="text/markdown")
    if format_name == "docx":
        return Response(
            to_docx(report),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=careersignal-report.docx"},
        )
    if format_name == "pdf":
        return Response(
            to_pdf(report),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=careersignal-report.pdf"},
        )
    raise HTTPException(status_code=404, detail="Supported formats: json, markdown, docx, pdf.")


@app.post("/api/profile")
async def update_profile(request: Request) -> dict[str, Any]:
    payload = await request.json()
    required = ("name", "degree", "year", "school", "skills", "interests", "goals", "experience")
    if any(not clean(payload.get(key)) for key in required):
        raise HTTPException(status_code=400, detail="All profile fields are required.")
    skills = payload["skills"]
    if isinstance(skills, str):
        skills = [item.strip() for item in re.split(r",|\n", skills) if item.strip()]
    if not isinstance(skills, list) or not skills:
        raise HTTPException(status_code=400, detail="Add at least one skill.")
    with DATA_LOCK:
        profile = load_profile()
        profile.update({key: clean(payload[key]) for key in required if key != "skills"})
        profile["skills"] = [clean(item) for item in skills[:12] if clean(item)]
        profile["updated_at"] = now()
        save_profile(profile)
        return state()


@app.post("/api/learning/toggle")
async def toggle_learning(request: Request) -> dict[str, Any]:
    payload = await request.json()
    index = payload.get("index")
    if not isinstance(index, int) or not 0 <= index <= 2:
        raise HTTPException(status_code=400, detail="Learning step index must be 0, 1, or 2.")
    with DATA_LOCK:
        profile = load_profile()
        profile["learning_completed"][index] = not profile["learning_completed"][index]
        profile["updated_at"] = now()
        save_profile(profile)
        return state()


@app.post("/api/uploads")
async def upload_evidence(request: Request) -> dict[str, Any]:
    payload = await request.json()
    original_name = Path(clean(payload.get("name"))).name
    encoded = payload.get("content")
    extension = Path(original_name).suffix.lower()
    if not original_name or extension not in ALLOWED_EXTENSIONS or not isinstance(encoded, str):
        raise HTTPException(status_code=400, detail="Unsupported or invalid upload.")
    try:
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as error:
        raise HTTPException(
            status_code=400, detail="Upload content is not valid base64."
        ) from error
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Upload exceeds the 6 MB limit.")
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "-", original_name).strip(".-")
    if not safe_name:
        raise HTTPException(status_code=400, detail="Upload filename is invalid.")
    with DATA_LOCK:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        (UPLOAD_DIR / safe_name).write_bytes(content)
        profile = load_profile()
        file_record = {"name": safe_name, "size": len(content), "uploaded_at": now()}
        profile["uploads"] = [
            item for item in profile.get("uploads", []) if item["name"] != safe_name
        ] + [file_record]
        profile["resume_analysis"] = analyse_evidence(safe_name, content)
        detected_skills = profile["resume_analysis"]["detected_skills"]
        profile["skills"] = list(dict.fromkeys(profile.get("skills", []) + detected_skills))[:15]
        if not profile.get("name") and profile["resume_analysis"].get("inferred_name"):
            profile["name"] = profile["resume_analysis"]["inferred_name"]
        profile["updated_at"] = now()
        save_profile(profile)
        return state()


@app.post("/api/uploads/delete")
async def delete_upload(request: Request) -> dict[str, Any]:
    payload = await request.json()
    name = Path(clean(payload.get("name"))).name
    if not name or name != clean(payload.get("name")):
        raise HTTPException(status_code=400, detail="Invalid upload filename.")
    with DATA_LOCK:
        target = (UPLOAD_DIR / name).resolve()
        if UPLOAD_DIR.resolve() not in target.parents:
            raise HTTPException(status_code=400, detail="Invalid upload path.")
        if not target.is_file():
            raise HTTPException(status_code=404, detail="Upload was not found.")
        target.unlink()
        profile = load_profile()
        profile["uploads"] = [item for item in profile.get("uploads", []) if item["name"] != name]
        profile["resume_analysis"] = (
            None if not profile["uploads"] else profile.get("resume_analysis")
        )
        profile["updated_at"] = now()
        save_profile(profile)
        return state()


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/{asset_path:path}", include_in_schema=False)
def static_asset(asset_path: str) -> FileResponse:
    if asset_path not in {"index.html", "script.js", "styles.css"}:
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(STATIC_DIR / asset_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("careersignal.api:app", host=settings.host, port=settings.port)
