# mono_gen

Generative art project based on StyleGAN-V for creating latent walk videos.

## Project Structure

```
mono_gen/
├── api/
│   ├── app.py               # Generator + latent walk implementation
│   ├── fastapi_app.py       # FastAPI server (serves UI too)
│   ├── requirements.txt     # Python dependencies
│   └── outputs/             # Generated videos (gitignored)
├── ui/
│   ├── index.html           # Main UI
│   ├── app.js              # UI logic
│   ├── styles.css          # Styling
│   └── config.js           # API configuration
├── .env.example            # Environment variables template
└── README.md
```

## Features

- **Asynchronous Generation**: Background job processing with real-time progress tracking
- **Latent Walk Generation**: Create smooth interpolations through StyleGAN latent space
- **Web UI**: Clean 3-step interface with live progress and logs
- **FastAPI Backend**: Robust API with job queue and status polling
- **RunPod Ready**: Optimized for RunPod deployment

## Quick Start (RunPod)

1. **Clone and setup**:
   ```bash
   cd ~/mono_gen
   git pull
   ```

2. **Install dependencies**:
   ```bash
   pip install -r api/requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your HuggingFace token and other settings
   ```

4. **Start the server**:
   ```bash
   cd api
   uvicorn fastapi_app:app --host 0.0.0.0 --port 8888 --workers 1
   ```

5. **Access the UI**: Open your RunPod HTTP link to port 8888

## API Endpoints

- `GET /` - Serves the UI
- `GET /healthz` - Health check
- `POST /generate` - Start latent walk video generation (returns job_id)
- `GET /status/{job_id}` - Get job status and progress
- `GET /download?path=<filename>` - Download generated video

If `API_KEY` is set in the environment the UI must send the key in an `X-API-Key`
header for API requests. The generated video download URL also accepts the key as an
`api_key` query parameter so that the `<video>` element can fetch the file without
custom headers.

### Job System

The API uses an asynchronous job system for video generation:

1. **Start Generation**: `POST /generate` returns immediately with a `job_id`
2. **Poll Status**: `GET /status/{job_id}` returns current progress and logs
3. **Download Result**: When complete, use the `download_url` from status

#### Status Response Format

```json
{
  "state": "queued|running|done|error",
  "progress": 0.0,           // 0..1
  "frames_done": 42,
  "total_frames": 900,
  "log_tail": ["Generated 30/900 frames", "..."],  // last ~50 lines
  "download_url": "/download?path=latent_walk_...mp4" // when state=done
}
```

### UI Flow

1. **Landing**: User clicks "INITIATE LATENT WALK"
2. **Progress**: UI polls `/status/{job_id}` every 2 seconds showing:
   - Progress bar (0-100%)
   - Frame count (e.g., "42/900 frames")
   - Live log output
3. **Preview**: When complete, shows video player with download link

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `MODEL_REPO`: HuggingFace model repository
- `CKPT_FILE`: Checkpoint filename
- `HF_TOKEN`: HuggingFace authentication token
- `API_KEY`: Optional API key for authentication

If you set `API_KEY`, the server now injects it into `/runtime-config.js` so the
frontend automatically authenticates every request and appends the key to the
video download URL.

### Runtime configuration exposed to the UI

The browser loads `/runtime-config.js`, which is generated at runtime from
environment variables:

| Variable        | Purpose                                              | Default           |
| --------------- | ----------------------------------------------------- | ----------------- |
| `API_KEY`       | API key required for UI/API access                    | *(empty)*         |
| `CKPT_FILE`     | Sets the displayed checkpoint lineage in the UI       | `checkpoint-13`   |
| `LOG_POLL_MS`   | Interval (ms) for refreshing the console log display  | `1000`            |

The Hugging Face credentials (`HF_TOKEN`, `MODEL_REPO`) and optional RunPod
`PUBLIC_KEY`/`JUPYTER_PASSWORD` values are consumed by other tooling and do not
need to be surfaced to the browser.

## Development

The project uses:
- **Backend**: FastAPI + PyTorch + StyleGAN-V
- **Frontend**: Vanilla JavaScript with modern UI
- **Deployment**: RunPod with uvicorn

## License

All rights reserved - mono-x 2025