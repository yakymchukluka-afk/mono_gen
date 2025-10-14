"""
FastAPI application for mono_gen video generator
Serves both API endpoints and static UI files
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app import gen_video

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# UI directory (parent of api directory)
UI_DIR = Path(__file__).resolve().parent.parent / "ui"

# Create FastAPI app
app = FastAPI(
    title="Latent Walk Video Generator",
    version="1.0.0",
    description="Generate StyleGAN-V based latent walk videos"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/generate")
async def generate_video(
    seconds: int = 2,
    fps: int = 8, 
    out_res: int = 256,
    anchors: int = 3,
    strength: float = 2.0,
    sharpen: bool = False,
    checkpoint: Optional[str] = None
):
    """
    Generate a latent walk video
    
    Args:
        seconds: Duration in seconds (default: 2)
        fps: Frames per second (default: 8)
        out_res: Output resolution (default: 256)
        anchors: Number of anchor points (default: 3)
        strength: Walk strength (default: 2.0)
        sharpen: Whether to apply sharpening (default: False)
        checkpoint: Model checkpoint to use (optional)
        
    Returns:
        Dict with video_path and download_url
    """
    try:
        logger.info(f"Generating video: {seconds}s, {fps}fps, {out_res}px")
        
        # Generate the video
        video_path = gen_video(
            seconds=seconds,
            fps=fps,
            out_res=out_res,
            anchors=anchors,
            strength=strength,
            sharpen=sharpen,
            checkpoint=checkpoint
        )
        
        # Convert to relative path for response
        video_path_obj = Path(video_path)
        relative_path = f"outputs/{video_path_obj.name}"
        
        # Create download URL
        download_url = f"/download?path={video_path_obj.name}"
        
        logger.info(f"Video generated: {video_path}")
        logger.info(f"Download URL: {download_url}")
        
        return {
            "video_path": relative_path,
            "download_url": download_url,
            "filename": video_path_obj.name
        }
        
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")

@app.get("/download")
@app.head("/download")
async def download_video(path: str = Query(..., description="Video filename (basename only)")):
    """
    Download a generated video file
    
    Args:
        path: Video filename (basename only for security)
        
    Returns:
        Video file
    """
    try:
        # Security: only allow basename to prevent directory traversal
        filename = Path(path).name
        full_path = OUTPUT_DIR / filename
        
        if not full_path.exists():
            logger.warning(f"Video not found: {filename}")
            raise HTTPException(status_code=404, detail="Video not found")
        
        logger.info(f"Serving video: {filename}")
        return FileResponse(
            str(full_path),
            media_type="video/mp4",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/logs")
async def get_logs(tail: int = 200):
    """
    Get recent logs
    
    Args:
        tail: Number of recent log lines to return
        
    Returns:
        Log content as plain text
    """
    try:
        # This is a simple implementation - in production you'd want proper log management
        return "Logs endpoint - implement proper log retrieval"
    except Exception as e:
        logger.error(f"Log retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Log retrieval failed: {str(e)}")

# Mount static UI files at root (after API routes)
app.mount("/", StaticFiles(directory=str(UI_DIR), html=True), name="ui")

if __name__ == "__main__":
    uvicorn.run(
        "fastapi_app:app",
        host="127.0.0.1",
        port=7777,
        workers=1,
        reload=False
    )