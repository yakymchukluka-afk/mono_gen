import os
import tempfile
import asyncio
import uuid
from fastapi import FastAPI, HTTPException, Header, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import uvicorn
from app import gen_video

app = FastAPI(title="Latent Walk Video Generator", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open for now as requested
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
API_KEY = os.getenv("API_KEY")

# In-memory storage for job status and results
job_status: Dict[str, Dict] = {}

class GenerateRequest(BaseModel):
    seconds: int = 30
    fps: int = 30
    out_res: int = 512
    anchors: int = 6
    strength: float = 2.0
    sharpen: bool = True

class GenerateResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    video_path: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None

def check_api_key(x_api_key: Optional[str] = Header(None)):
    """Check API key if required"""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

async def generate_video_background(job_id: str, request: GenerateRequest):
    """Background task to generate video"""
    try:
        # Update status to processing
        job_status[job_id] = {
            "status": "processing",
            "message": "Generating video...",
            "video_path": None,
            "download_url": None,
            "error": None
        }
        
        # Generate video (this runs in a thread pool to avoid blocking)
        loop = asyncio.get_event_loop()
        video_path = await loop.run_in_executor(
            None, 
            gen_video,
            request.seconds,
            request.fps,
            request.out_res,
            request.anchors,
            request.strength,
            request.sharpen
        )
        
        # Create download URL
        download_url = f"/download?path={os.path.basename(video_path)}"
        
        # Update status to completed
        job_status[job_id] = {
            "status": "completed",
            "message": "Video generated successfully!",
            "video_path": video_path,
            "download_url": download_url,
            "error": None
        }
        
    except Exception as e:
        # Update status to error
        job_status[job_id] = {
            "status": "error",
            "message": "Video generation failed",
            "video_path": None,
            "download_url": None,
            "error": str(e)
        }

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"ok": True}

@app.post("/generate", response_model=GenerateResponse)
async def generate_video(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None)
):
    """Start generating a latent walk video"""
    # Check API key if required
    if API_KEY:
        check_api_key(x_api_key)
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    job_status[job_id] = {
        "status": "queued",
        "message": "Video generation queued...",
        "video_path": None,
        "download_url": None,
        "error": None
    }
    
    # Start background task
    background_tasks.add_task(generate_video_background, job_id, request)
    
    return GenerateResponse(
        job_id=job_id,
        status="queued",
        message="Video generation started. Use the job_id to check status."
    )

@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    x_api_key: Optional[str] = Header(None)
):
    """Get the status of a video generation job"""
    # Check API key if required
    if API_KEY:
        check_api_key(x_api_key)
    
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = job_status[job_id]
    return JobStatusResponse(
        job_id=job_id,
        status=job_data["status"],
        video_path=job_data["video_path"],
        download_url=job_data["download_url"],
        error=job_data["error"]
    )

@app.get("/download")
async def download_video(
    path: str = Query(..., description="Video file path"),
    x_api_key: Optional[str] = Header(None)
):
    """Download generated video"""
    # Check API key if required
    if API_KEY:
        check_api_key(x_api_key)
    
    # Security check: ensure path is in outputs directory
    full_path = os.path.join("outputs", path)
    if not os.path.exists(full_path) or not full_path.startswith(os.path.abspath("outputs")):
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Return file as streaming response
    return FileResponse(
        full_path,
        media_type="video/mp4",
        filename=os.path.basename(full_path)
    )

if __name__ == "__main__":
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=8888,
        reload=False
    )