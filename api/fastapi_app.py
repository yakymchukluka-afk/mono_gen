import os
import tempfile
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
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
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Job management
jobs: Dict[str, Dict] = {}

class GenerateRequest(BaseModel):
    seconds: int = 30
    fps: int = 30
    out_res: int = 512
    anchors: int = 6
    strength: float = 2.0
    sharpen: bool = True

class GenerateResponse(BaseModel):
    job_id: str

class StatusResponse(BaseModel):
    state: str  # "queued", "running", "done", "error"
    progress: float  # 0.0 to 1.0
    frames_done: int
    total_frames: int
    log_tail: List[str]
    download_url: Optional[str] = None

def check_api_key(x_api_key: Optional[str] = Header(None)):
    """Check API key if required"""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

async def background_generate_video(job_id: str, request: GenerateRequest):
    """Background task to generate video"""
    try:
        # Update job status to running
        jobs[job_id]["state"] = "running"
        jobs[job_id]["started_at"] = datetime.now()
        
        # Calculate total frames
        total_frames = request.seconds * request.fps
        jobs[job_id]["total_frames"] = total_frames
        
        # Create a custom gen_video function that reports progress
        def gen_video_with_progress():
            return gen_video_with_progress_tracking(
                job_id=job_id,
                seconds=request.seconds,
                fps=request.fps,
                out_res=request.out_res,
                anchors=request.anchors,
                strength=request.strength,
                sharpen=request.sharpen
            )
        
        # Generate video
        video_path = gen_video_with_progress()
        
        # Update job status to done
        jobs[job_id]["state"] = "done"
        jobs[job_id]["video_path"] = video_path
        jobs[job_id]["download_url"] = f"/download?path={Path(video_path).name}"
        jobs[job_id]["completed_at"] = datetime.now()
        
    except Exception as e:
        # Update job status to error
        jobs[job_id]["state"] = "error"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now()
        print(f"Job {job_id} failed: {e}")

def gen_video_with_progress_tracking(
    job_id: str,
    seconds: int = 30,
    fps: int = 30,
    out_res: int = 512,
    anchors: int = 6,
    strength: float = 2.0,
    sharpen: bool = True
) -> str:
    """Generate video with progress tracking"""
    from app import get_G, generate_anchors, interpolate_latent_walk, tensor_to_pil, sharpen_image
    import torch
    import imageio
    import numpy as np
    from PIL import Image
    
    print(f"Job {job_id}: Generating video: {seconds}s @ {fps}fps, resolution {out_res}x{out_res}")
    
    # Load generator
    generator = get_G()
    generator.eval()
    
    # Generate anchors
    anchors_tensor = generate_anchors(z_dim=128, anchors=anchors, strength=strength)
    
    # Calculate total frames
    total_frames = seconds * fps
    
    # Interpolate latent walk
    latent_walk = interpolate_latent_walk(anchors_tensor, total_frames)
    
    # Generate frames
    frames = []
    with torch.no_grad():
        for i, z in enumerate(latent_walk):
            z = z.unsqueeze(0)  # Add batch dimension
            generated = generator(z)
            
            # Convert to PIL
            frame = tensor_to_pil(generated)
            
            # Apply sharpening if requested
            if sharpen:
                frame = sharpen_image(frame)
            
            frames.append(frame)
            
            # Update progress
            frames_done = i + 1
            progress = frames_done / total_frames
            
            # Update job status
            jobs[job_id]["frames_done"] = frames_done
            jobs[job_id]["progress"] = progress
            
            # Add log entry
            log_entry = f"Generated {frames_done}/{total_frames} frames ({progress:.1%})"
            jobs[job_id]["log_tail"].append(log_entry)
            
            # Keep only last 50 log entries
            if len(jobs[job_id]["log_tail"]) > 50:
                jobs[job_id]["log_tail"] = jobs[job_id]["log_tail"][-50:]
            
            print(f"Job {job_id}: {log_entry}")
            
            if frames_done % 30 == 0:
                print(f"Job {job_id}: Generated {frames_done}/{total_frames} frames")
    
    # Save video to OUTPUT_DIR
    output_path = OUTPUT_DIR / f"latent_walk_{seconds}s_{fps}fps_{job_id[:8]}.mp4"
    
    # Use imageio-ffmpeg to write MP4
    writer = imageio.get_writer(str(output_path), fps=fps, codec='libx264')
    for frame in frames:
        writer.append_data(np.array(frame))
    writer.close()
    
    print(f"Job {job_id}: Video saved to: {output_path}")
    return str(output_path)

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
    """Generate a latent walk video asynchronously"""
    # Check API key if required
    if API_KEY:
        check_api_key(x_api_key)
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    jobs[job_id] = {
        "state": "queued",
        "progress": 0.0,
        "frames_done": 0,
        "total_frames": 0,
        "log_tail": [],
        "created_at": datetime.now(),
        "request": request.dict()
    }
    
    # Start background task
    background_tasks.add_task(background_generate_video, job_id, request)
    
    return GenerateResponse(job_id=job_id)

@app.get("/status/{job_id}", response_model=StatusResponse)
async def get_job_status(
    job_id: str,
    x_api_key: Optional[str] = Header(None)
):
    """Get job status and progress"""
    # Check API key if required
    if API_KEY:
        check_api_key(x_api_key)
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    return StatusResponse(
        state=job["state"],
        progress=job["progress"],
        frames_done=job["frames_done"],
        total_frames=job["total_frames"],
        log_tail=job["log_tail"],
        download_url=job.get("download_url")
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
    
    # Security: accept only basenames and read from OUTPUT_DIR
    fname = Path(path).name
    full_path = OUTPUT_DIR / fname
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Return file as streaming response
    return FileResponse(
        str(full_path),
        media_type="video/mp4",
        filename=fname
    )

# Mount UI static files
app.mount("/", StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "ui"), html=True), name="ui")

if __name__ == "__main__":
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=8888,
        reload=False
    )