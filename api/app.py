import os
import torch
import torch.nn as nn
import numpy as np
import imageio
from PIL import Image
from huggingface_hub import hf_hub_download
import tempfile
import shutil
from typing import Optional, Tuple
from pathlib import Path

# Configuration
MODEL_REPO = os.getenv("MODEL_REPO", "lukua/mono-poc")
CKPT_FILE = os.getenv("CKPT_FILE", "monox_generator_1400.pth")
HF_TOKEN = os.getenv("HF_TOKEN")
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class TinyG(nn.Module):
    """Fallback generator that creates simple 64x64 images upscaled to target resolution"""
    def __init__(self, z_dim=128, out_res=512):
        super().__init__()
        self.z_dim = z_dim
        self.out_res = out_res
        
        # Simple generator: z -> 64x64 -> upscale to target
        self.main = nn.Sequential(
            nn.Linear(z_dim, 64 * 64 * 3),
            nn.Tanh()
        )
        
    def forward(self, z):
        batch_size = z.shape[0]
        x = self.main(z)
        x = x.view(batch_size, 3, 64, 64)
        # Upscale to target resolution
        x = torch.nn.functional.interpolate(x, size=(self.out_res, self.out_res), mode='bilinear', align_corners=False)
        return x

def load_checkpoint() -> Optional[torch.nn.Module]:
    """Load the HuggingFace checkpoint, fallback to TinyG if not available"""
    try:
        print(f"Attempting to load checkpoint from {MODEL_REPO}/{CKPT_FILE}")
        
        # Download checkpoint
        checkpoint_path = hf_hub_download(
            repo_id=MODEL_REPO,
            filename=CKPT_FILE,
            token=HF_TOKEN
        )
        
        # Load checkpoint
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        
        # Try to extract generator state dict
        if "generator_state_dict" in checkpoint:
            print("Found generator_state_dict in checkpoint")
            # For now, we'll use TinyG as the actual model structure is unknown
            # In a real implementation, you'd load the actual generator architecture
            generator = TinyG()
            generator.load_state_dict(checkpoint["generator_state_dict"])
            return generator
        else:
            print("No generator_state_dict found in checkpoint, using TinyG fallback")
            return TinyG()
            
    except Exception as e:
        print(f"Failed to load checkpoint: {e}")
        print("Using TinyG fallback")
        return TinyG()

def generate_anchors(z_dim=128, anchors=6, strength=2.0) -> torch.Tensor:
    """Generate anchor points in latent space"""
    # Generate random anchor points
    anchors_tensor = torch.randn(anchors, z_dim) * strength
    return anchors_tensor

def interpolate_latent_walk(anchors: torch.Tensor, total_frames: int) -> torch.Tensor:
    """Interpolate between anchors to create smooth latent walk"""
    anchors = anchors.cpu().numpy()
    total_frames = int(total_frames)
    
    # Create interpolation indices
    indices = np.linspace(0, len(anchors) - 1, total_frames)
    
    # Interpolate between anchors
    interpolated = []
    for i in indices:
        idx = int(i)
        if idx == len(anchors) - 1:
            interpolated.append(anchors[idx])
        else:
            # Linear interpolation between current and next anchor
            alpha = i - idx
            interpolated.append(anchors[idx] * (1 - alpha) + anchors[idx + 1] * alpha)
    
    return torch.tensor(np.array(interpolated), dtype=torch.float32)

def tensor_to_pil(tensor: torch.Tensor) -> Image.Image:
    """Convert tensor to PIL Image"""
    # Ensure tensor is in [0, 1] range
    tensor = (tensor + 1) / 2  # Convert from [-1, 1] to [0, 1]
    tensor = torch.clamp(tensor, 0, 1)
    
    # Convert to numpy and transpose for PIL
    array = tensor.detach().cpu().numpy()
    array = (array * 255).astype(np.uint8)
    
    # Handle batch dimension
    if len(array.shape) == 4:
        array = array[0]  # Take first image from batch
    
    # Transpose from CHW to HWC
    array = np.transpose(array, (1, 2, 0))
    
    return Image.fromarray(array)

def sharpen_image(image: Image.Image) -> Image.Image:
    """Apply sharpening filter (no-op for now as requested)"""
    # This is a no-op as requested in the requirements
    return image

def gen_video(
    seconds: int = 30,
    fps: int = 30,
    out_res: int = 512,
    anchors: int = 6,
    strength: float = 2.0,
    sharpen: bool = True
) -> str:
    """Generate a latent walk video"""
    print(f"Generating video: {seconds}s @ {fps}fps, resolution {out_res}x{out_res}")
    
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
            
            if (i + 1) % 30 == 0:
                print(f"Generated {i + 1}/{total_frames} frames")
    
    # Save video to OUTPUT_DIR
    output_path = OUTPUT_DIR / f"latent_walk_{seconds}s_{fps}fps.mp4"
    
    # Use imageio-ffmpeg to write MP4
    writer = imageio.get_writer(str(output_path), fps=fps, codec='libx264')
    for frame in frames:
        writer.append_data(np.array(frame))
    writer.close()
    
    print(f"Video saved to: {output_path}")
    return str(output_path)

# Global generator instance
_G = None

def get_G() -> torch.nn.Module:
    """Get or create the generator instance"""
    global _G
    if _G is None:
        _G = load_checkpoint()
    return _G

if __name__ == "__main__":
    # Test the generator
    print("Testing generator...")
    generator = get_G()
    print(f"Generator loaded: {type(generator).__name__}")
    
    # Generate a test video
    video_path = gen_video(seconds=5, fps=10, out_res=256)
    print(f"Test video generated: {video_path}")