# mono_gen

Generative art project based on StyleGAN-V for creating latent walk videos.

## Quick Start (RunPod)

1. **Clone and setup:**
   ```bash
   cd ~/mono_gen
   pip install -r api/requirements.txt
   ```

2. **Configure environment (optional):**
   ```bash
   cp .env.example .env
   # Edit .env with your settings if needed
   ```

3. **Start the server:**
   ```bash
   uvicorn api.fastapi_app:app --host 0.0.0.0 --port 8888 --workers 1
   ```

4. **Access the UI:**
   - Open your browser to `http://localhost:8888`
   - Click "INITIATE LATENT WALK" to generate a video

## Environment Variables

Create a `.env` file with the following variables:

- `MODEL_REPO`: Hugging Face repository (default: `mono-x/stylegan-v`)
- `CKPT_FILE`: Checkpoint filename (default: `checkpoint-13.ckpt`)
- `HF_TOKEN`: Hugging Face token (optional, can be empty for public repos)
- `API_KEY`: API key for authentication (optional)

## API Endpoints

- `GET /` - Serves the UI
- `POST /generate` - Generate a video
- `GET /download?path=<filename>` - Download a generated video
- `GET /health` - Health check
- `GET /logs?tail=<n>` - Get recent logs

## Project Structure

```
mono_gen/
├── api/
│   ├── app.py              # Video generation logic
│   ├── fastapi_app.py      # FastAPI server
│   ├── requirements.txt    # Python dependencies
│   └── outputs/            # Generated videos (gitignored)
├── ui/
│   ├── index.html          # Main UI
│   ├── app.js              # Frontend logic
│   ├── styles.css          # Styling
│   └── config.js           # Configuration
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Testing

Test the API with curl:

```bash
# Generate a video
curl -s -X POST http://127.0.0.1:8888/generate \
  -H 'content-type: application/json' \
  -d '{"seconds":2,"fps":8,"out_res":256,"anchors":3,"strength":2.0,"sharpen":false}' | tee /tmp/r.json

# Check download works
curl -I "http://127.0.0.1:8888$(jq -r .download_url /tmp/r.json)"
```

## Development

The project uses FastAPI for the backend and vanilla JavaScript for the frontend. The UI is served as static files from the same origin as the API to avoid CORS issues.

## License

All rights reserved - mono-x 2025