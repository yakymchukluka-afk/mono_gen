import os
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
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

class GenerateRequest(BaseModel):
    seconds: int = 30
    fps: int = 30
    out_res: int = 512
    anchors: int = 6
    strength: float = 2.0
    sharpen: bool = True

class GenerateResponse(BaseModel):
    video_path: str
    download_url: str

def check_api_key(x_api_key: Optional[str] = Header(None)):
    """Check API key if required"""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"ok": True}

@app.post("/generate", response_model=GenerateResponse)
async def generate_video(
    request: GenerateRequest,
    x_api_key: Optional[str] = Header(None)
):
    """Generate a latent walk video"""
    # Check API key if required
    if API_KEY:
        check_api_key(x_api_key)
    
    try:
        # Generate video
        video_path = gen_video(
            seconds=request.seconds,
            fps=request.fps,
            out_res=request.out_res,
            anchors=request.anchors,
            strength=request.strength,
            sharpen=request.sharpen
        )
        
        # Create download URL using only the basename for security
        download_url = f"/download?path={Path(video_path).name}"
        
        return GenerateResponse(
            video_path=video_path,
            download_url=download_url
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")

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