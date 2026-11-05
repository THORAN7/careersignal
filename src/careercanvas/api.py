"""FastAPI application entry point for CareerCanvas.

The typed domain and generation pipeline are introduced in later phases.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from .config import settings

ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = ROOT / "static"

app = FastAPI(title="CareerCanvas", version="0.1.0")


@app.get("/api/health")
def health() -> dict[str, bool | str]:
    """Return a lightweight service health response."""

    return {"ok": True, "service": "careercanvas"}


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
