from pathlib import Path
import re
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from .scheduler import start_scheduler
from .pipeline import run_daily_pipeline
from .utils import load_json
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
BASE_DIR = Path(__file__).resolve().parent.parent
POSTERS_DIR = BASE_DIR / "posters"
DEEP_DIVE_DIR = BASE_DIR / "deep_dive_articles"
SAFE_FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

def _safe_file_path(base_dir: Path, filename: str):
    if not SAFE_FILENAME_PATTERN.fullmatch(filename):
        return None
    if not base_dir.exists():
        return None
    files_by_name = {path.name: path for path in base_dir.iterdir() if path.is_file()}
    return files_by_name.get(filename)

@app.on_event("startup")
def startup():
    start_scheduler()

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/dashboard")
def dashboard():
    try:
        return JSONResponse(load_json('daily_results_latest.json'))
    except:
        return JSONResponse({"error": "No data yet"}, status_code=404)

@app.post("/api/refresh")
async def refresh(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_daily_pipeline)
    return {"status": "pipeline started"}

@app.get("/api/poster/{filename}")
def poster(filename: str):
    safe_path = _safe_file_path(POSTERS_DIR, filename)
    if safe_path:
        return FileResponse(safe_path, media_type="image/png", filename=safe_path.name)
    return JSONResponse({"error": "not found"}, 404)

@app.get("/api/deep-dive/{filename}")
def deep_dive(filename: str):
    safe_path = _safe_file_path(DEEP_DIVE_DIR, filename)
    if safe_path:
        return FileResponse(safe_path, media_type="application/json", filename=safe_path.name)
    return JSONResponse({"error": "not found"}, 404)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)