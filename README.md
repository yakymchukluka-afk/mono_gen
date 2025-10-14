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

- **Latent Walk Generation**: Create smooth interpolations through StyleGAN latent space
- **Web UI**: Clean 3-step interface for generation and preview
- **FastAPI Backend**: Robust API with proper error handling
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
- `POST /generate` - Generate latent walk video
- `GET /download?path=<filename>` - Download generated video

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `MODEL_REPO`: HuggingFace model repository
- `CKPT_FILE`: Checkpoint filename
- `HF_TOKEN`: HuggingFace authentication token
- `API_KEY`: Optional API key for authentication

## Development

The project uses:
- **Backend**: FastAPI + PyTorch + StyleGAN-V
- **Frontend**: Vanilla JavaScript with modern UI
- **Deployment**: RunPod with uvicorn

## License

All rights reserved - mono-x 2025