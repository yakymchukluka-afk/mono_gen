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
│   └── styles.css          # Styling
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

1. **Clone or update the repository**
   ```bash
   cd /workspace
   # First-time pod: git clone https://github.com/<your-org>/mono_gen.git
   cd mono_gen
   git pull  # no-op if you just cloned
   ```
   > ℹ️ Run the rest of the commands from `/workspace/mono_gen`. The helper script
   > resolves its own path, so you can invoke it with `bash setup_runpod.sh` from
   > anywhere, but the manual commands below assume you are in the repo root.

2. **Provide the required environment variables in RunPod**
   - `MODEL_REPO` – Hugging Face repository containing your weights
   - `CKPT_FILE` – checkpoint filename inside the repo
   - `HF_TOKEN` – Hugging Face token with access to the checkpoint
   - `API_KEY` – (optional) string your UI will use for authenticated calls

   Set these in the **Environment Variables** section of your RunPod template or pod. The backend reads them on startup and `/runtime-config.js` automatically exposes the safe values (API key, checkpoint name, polling interval) to the browser.

3. **Launch the automated setup**
   ```bash
   bash setup_runpod.sh
   ```
    The script installs CUDA-enabled PyTorch, project dependencies, verifies the UI assets, and starts `uvicorn` on port 8888. Logs stream to `/workspace/mono_gen/server.log`.

4. **Open the UI**
   Visit the HTTPS link that RunPod provides for port 8888. The page will fetch `/runtime-config.js`, attach your API key to every request, and handle video downloads.

5. **Monitor or restart as needed**
   ```bash
    tail -f /workspace/mono_gen/server.log   # live logs
   pkill -f uvicorn               # stop the server
   bash setup_runpod.sh           # rerun setup/start
   ```

### Manual startup (advanced)

If you prefer to control each step yourself:

1. Install dependencies
   ```bash
   cd /workspace/mono_gen
   pip install --extra-index-url https://download.pytorch.org/whl/cu121 \
     torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2
   pip install -r api/requirements.txt
   ```

2. Export the same environment variables that you configured in RunPod (for local shells you can `cp .env.example .env` and fill it in).

3. Start the server from the repository root
   ```bash
   cd /workspace/mono_gen
   uvicorn api.fastapi_app:app --host 0.0.0.0 --port 8888 --workers 1
   ```

4. Open the RunPod HTTP URL for port 8888. The UI will automatically read `/runtime-config.js`, send the `X-API-Key` header when required, and append `?api_key=...` to the video preview URL.

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