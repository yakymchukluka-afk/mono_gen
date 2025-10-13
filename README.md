# Latent Walk Video Generator

A complete system for generating smooth latent space walk videos using AI models.

## Project Structure

This repository contains two main components:

- **API**: FastAPI service for video generation
- **UI**: Web interface for interacting with the API

## Quick Start

### 1. API (Backend)

See the [API README](ui/README.md) for detailed setup instructions.

**RunPod Deployment:**
```bash
# Install PyTorch with CUDA support
pip install --extra-index-url https://download.pytorch.org/whl/cu121 \
    torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2

# Install requirements
pip install -r requirements.txt

# Set environment variables (optional)
export HF_TOKEN="your_hf_token_here"
export API_KEY="your_api_key_here"

# Run the service
uvicorn fastapi_app:app --host 0.0.0.0 --port 8888
```

### 2. UI (Frontend)

```bash
cd ui
cp config.example.js config.js
# Edit config.js to point to your API
python -m http.server 3000
# Open http://localhost:3000
```

## Features

- **Latent Walk Generation**: Smooth interpolation through latent space
- **HuggingFace Integration**: Loads models from HF Hub
- **Fallback Generator**: TinyG when HF model unavailable
- **RESTful API**: Clean FastAPI endpoints
- **Responsive UI**: Modern web interface
- **Authentication**: Optional API key protection
- **Video Export**: MP4 output with configurable parameters

## API Endpoints

- `GET /healthz` - Health check
- `POST /generate` - Generate video
- `GET /download?path=<file>` - Download video

## Configuration

### Environment Variables

- `HF_TOKEN`: HuggingFace token for private repos
- `API_KEY`: API key for authentication (optional)

### Model Configuration

- **Repository**: `lukua/mono-poc`
- **Checkpoint**: `monox_generator_1400.pth`
- **Fallback**: TinyG generator (64×64 → upscaled)

## License

This project is part of the mono_gen repository.