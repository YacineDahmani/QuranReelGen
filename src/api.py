import os
import uuid
import threading
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import OUTPUT_DIR
from .models import ReelRequest
from .core import process_job

app = FastAPI(title="Quran Reel Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global jobs state
jobs = {}

@app.post("/generate")
async def generate_reel(req: ReelRequest):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "result_url": None,
        "error": None
    }
    
    # Start background thread
    thread = threading.Thread(target=process_job, args=(job_id, req, jobs), daemon=True)
    thread.start()
    
    return {"job_id": job_id}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Inject result_url if completed
    if jobs[job_id]["status"] == "completed" and not jobs[job_id]["result_url"]:
        filename = f"output_{job_id}.mp4"
        jobs[job_id]["result_url"] = f"/download/{filename}"
        
    return jobs[job_id]

@app.get("/download/{filename}")
async def download_video(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="video/mp4", filename=filename)

def start_api(host="0.0.0.0", port=8001):
    import uvicorn
    # Serve Frontend if it exists in current dir
    if os.path.exists("index.html"):
         app.mount("/", StaticFiles(directory=".", html=True), name="static")
    
    uvicorn.run(app, host=host, port=port)
