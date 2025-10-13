# Latent Walk Video Generator API

A FastAPI service that generates 30-second latent walk videos using HuggingFace checkpoints or a fallback generator.

## RunPod Deployment

### 1. Install PyTorch with CUDA 12.1 support

```bash
pip install --extra-index-url https://download.pytorch.org/whl/cu121 \
    torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2
```

### 2. Install requirements

```bash
pip install -r requirements.txt
```

### 3. Set environment variables (optional)

```bash
# Optional: HuggingFace token for private repos
export HF_TOKEN="your_hf_token_here"

# Optional: API key for authentication
export API_KEY="your_api_key_here"
```

### 4. Run the service

```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 8888
```

The API will be available at `http://0.0.0.0:8888`

## API Endpoints

### Health Check
- **GET** `/healthz` - Returns `{"ok": true}`

### Generate Video
- **POST** `/generate` - Generate a latent walk video
- **Headers**: `X-API-Key` (optional, if API_KEY env var is set)
- **Body**:
  ```json
  {
    "seconds": 30,
    "fps": 30,
    "out_res": 512,
    "anchors": 6,
    "strength": 2.0,
    "sharpen": true
  }
  ```
- **Response**:
  ```json
  {
    "video_path": "outputs/latent_walk_30s_30fps.mp4",
    "download_url": "/download?path=latent_walk_30s_30fps.mp4"
  }
  ```

### Download Video
- **GET** `/download?path=<filename>` - Download generated video
- **Headers**: `X-API-Key` (optional, if API_KEY env var is set)

## Model Loading

The service attempts to load the checkpoint from:
- **Repository**: `lukua/mono-poc`
- **File**: `monox_generator_1400.pth`
- **Key**: `generator_state_dict`

If the checkpoint is missing or incompatible, it falls back to a simple TinyG generator that creates 64×64 images upscaled to the target resolution.

## Configuration

- **Default video**: 30 seconds @ 30fps, 512×512 resolution
- **Latent space**: 128-dimensional
- **Anchors**: 6 waypoints for smooth interpolation
- **Strength**: 2.0 (controls latent space exploration)
- **Output directory**: `outputs/`

## Testing

Test the API locally:

```bash
# Health check
curl http://localhost:8888/healthz

# Generate video (no auth)
curl -X POST http://localhost:8888/generate \
  -H "Content-Type: application/json" \
  -d '{"seconds": 5, "fps": 10, "out_res": 256}'

# Generate video (with auth)
curl -X POST http://localhost:8888/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{"seconds": 30, "fps": 30}'
```