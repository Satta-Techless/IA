import os
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from .scheduler import start_scheduler
from .pipeline import run_daily_pipeline
from .utils import load_json
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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
    path = f"posters/{filename}"
    if os.path.exists(path):
        return FileResponse(path, media_type="image/png", filename=filename)
    return JSONResponse({"error": "not found"}, 404)

@app.get("/api/deep-dive/{filename}")
def deep_dive(filename: str):
    path = f"deep_dive_articles/{filename}"
    if os.path.exists(path):
        return FileResponse(path, media_type="application/json", filename=filename)
    return JSONResponse({"error": "not found"}, 404)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)