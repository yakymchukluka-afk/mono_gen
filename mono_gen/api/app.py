"""
Video generation module for mono_gen
Handles StyleGAN-V based latent walk video generation
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import torch
import numpy as np
from PIL import Image
import cv2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model configuration
MODEL_REPO = os.getenv("MODEL_REPO", "mono-x/stylegan-v")
CKPT_FILE = os.getenv("CKPT_FILE", "checkpoint-13.ckpt")
HF_TOKEN = os.getenv("HF_TOKEN", "")

class VideoGenerator:
    def __init__(self):
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
    def load_model(self, checkpoint: str = None):
        """Load the StyleGAN-V model"""
        try:
            if checkpoint is None:
                checkpoint = CKPT_FILE
                
            logger.info(f"Loading model from {MODEL_REPO} with checkpoint {checkpoint}")
            
            # Try to load from Hugging Face
            try:
                from huggingface_hub import hf_hub_download
                model_path = hf_hub_download(
                    repo_id=MODEL_REPO,
                    filename=checkpoint,
                    token=HF_TOKEN if HF_TOKEN else None
                )
                logger.info(f"Downloaded model to: {model_path}")
            except Exception as e:
                logger.warning(f"Failed to download from HF: {e}")
                # Fallback to local model loading
                model_path = f"models/{checkpoint}"
                if not os.path.exists(model_path):
                    raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # Load the model (simplified - you may need to adjust based on actual model structure)
            # This is a placeholder - replace with actual model loading code
            self.model = {"checkpoint": checkpoint, "path": model_path}
            logger.info("Model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def generate_latent_walk(self, seconds: int = 2, fps: int = 8, out_res: int = 256, 
                           anchors: int = 3, strength: float = 2.0, sharpen: bool = False) -> str:
        """
        Generate a latent walk video
        
        Args:
            seconds: Duration in seconds
            fps: Frames per second
            out_res: Output resolution
            anchors: Number of anchor points
            strength: Walk strength
            sharpen: Whether to apply sharpening
            
        Returns:
            Path to generated video file
        """
        try:
            if self.model is None:
                if not self.load_model():
                    raise RuntimeError("Failed to load model")
            
            logger.info(f"Generating video: {seconds}s, {fps}fps, {out_res}px, {anchors} anchors")
            
            # Calculate number of frames
            num_frames = seconds * fps
            
            # Generate latent codes for the walk
            latent_codes = self._generate_latent_codes(num_frames, anchors, strength)
            
            # Generate frames
            frames = []
            for i, latent in enumerate(latent_codes):
                frame = self._generate_frame(latent, out_res, sharpen)
                frames.append(frame)
                
                # Update progress
                progress = (i + 1) / num_frames * 100
                logger.info(f"Generated frame {i+1}/{num_frames} ({progress:.1f}%)")
            
            # Create video
            output_path = self._create_video(frames, fps, seconds)
            
            logger.info(f"Video generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            raise
    
    def _generate_latent_codes(self, num_frames: int, anchors: int, strength: float) -> np.ndarray:
        """Generate latent codes for the walk"""
        # Create anchor points in latent space
        anchor_points = np.random.randn(anchors, 512)  # Assuming 512-dim latent space
        
        # Interpolate between anchor points
        latent_codes = []
        for i in range(num_frames):
            t = i / (num_frames - 1) if num_frames > 1 else 0
            # Simple linear interpolation between first and last anchor
            latent = anchor_points[0] * (1 - t) + anchor_points[-1] * t
            # Add some noise for variation
            latent += np.random.randn(512) * 0.1 * strength
            latent_codes.append(latent)
        
        return np.array(latent_codes)
    
    def _generate_frame(self, latent: np.ndarray, resolution: int, sharpen: bool) -> np.ndarray:
        """Generate a single frame from latent code"""
        # This is a placeholder - replace with actual StyleGAN-V inference
        # For now, generate a simple gradient pattern
        frame = np.random.rand(resolution, resolution, 3) * 255
        frame = frame.astype(np.uint8)
        
        if sharpen:
            # Apply simple sharpening
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            frame = cv2.filter2D(frame, -1, kernel)
            frame = np.clip(frame, 0, 255)
        
        return frame
    
    def _create_video(self, frames: list, fps: int, duration: int) -> str:
        """Create video from frames"""
        from pathlib import Path
        
        # Ensure output directory exists
        output_dir = Path(__file__).parent / "outputs"
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = int(time.time())
        filename = f"latent_walk_{duration}s_{fps}fps_{timestamp}.mp4"
        output_path = output_dir / filename
        
        # Create video writer
        height, width = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        # Write frames
        for frame in frames:
            # Convert RGB to BGR for OpenCV
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            writer.write(frame_bgr)
        
        writer.release()
        
        return str(output_path)

# Global generator instance
generator = VideoGenerator()

def gen_video(seconds: int = 2, fps: int = 8, out_res: int = 256, 
              anchors: int = 3, strength: float = 2.0, sharpen: bool = False,
              checkpoint: str = None) -> str:
    """
    Generate a latent walk video
    
    Args:
        seconds: Duration in seconds
        fps: Frames per second  
        out_res: Output resolution
        anchors: Number of anchor points
        strength: Walk strength
        sharpen: Whether to apply sharpening
        checkpoint: Model checkpoint to use
        
    Returns:
        Path to generated video file
    """
    return generator.generate_latent_walk(
        seconds=seconds, fps=fps, out_res=out_res,
        anchors=anchors, strength=strength, sharpen=sharpen
    )