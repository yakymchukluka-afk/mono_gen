#!/bin/bash

# mono_gen RunPod Setup Script
# Sets up and runs the asynchronous video generation API

set -e  # Exit on any error

echo "🚀 Setting up mono_gen on RunPod..."

# Step 1 — switch to main branch and pull
echo "📥 Step 1: Updating repository..."
cd ~/mono_gen
git fetch --all
git checkout main
git pull

# Step 2 — detect where the app lives (our structure)
echo "🔍 Step 2: Detecting application structure..."
if [ -f api/fastapi_app.py ]; then
  export APP="api.fastapi_app:app" 
  export REQ="api/requirements.txt"
  echo "✅ Found API in api/ directory"
elif [ -f fastapi_app.py ]; then
  export APP="fastapi_app:app" 
  export REQ="requirements.txt"
  echo "✅ Found API in root directory"
else
  echo "❌ No fastapi_app.py found!"
  echo "Available files:"
  ls -la
  echo "Available branches:"
  git branch -a
  exit 1
fi
echo "APP=$APP  REQ=$REQ"

# Step 3 — install dependencies (Torch + project)
echo "📦 Step 3: Installing dependencies..."

# Clean up any broken torch leftovers (harmless if nothing to remove)
echo "🧹 Cleaning up old PyTorch installations..."
pip uninstall -y torch torchvision torchaudio >/dev/null 2>&1 || true
find /usr/local/lib/python3.12/dist-packages -maxdepth 1 -name "*~orch*" -exec rm -rf {} + 2>/dev/null || true

# Install PyTorch with CUDA support
echo "🔥 Installing PyTorch with CUDA support..."
pip install --extra-index-url https://download.pytorch.org/whl/cu121 \
  torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 -q

# Install project dependencies
echo "📚 Installing project dependencies..."
if [ -f "$REQ" ]; then
  pip install -r "$REQ" -q
  echo "✅ Installed from $REQ"
else
  echo "⚠️  Requirements file not found, installing basic dependencies..."
  pip install -q fastapi==0.119.0 uvicorn==0.37.0 imageio==2.37.0 imageio-ffmpeg==0.6.0 numpy==1.26.4 huggingface_hub psutil pillow
fi

# Step 4 — ensure the UI is present and configured
echo "🎨 Step 4: Configuring UI..."

# Check if UI directory exists
if [ ! -d ui ]; then
  echo "❌ UI directory not found!"
  echo "Available directories:"
  ls -la
  exit 1
fi

# Configure UI for same-origin calls and no API key
echo "⚙️  Configuring UI for same-origin API calls..."
if [ -f ui/config.js ]; then
  sed -i 's#API_BASE: .*#API_BASE: ""#; s#API_KEY: .*#API_KEY: ""#' ui/config.js
  echo "✅ Updated ui/config.js"
else
  echo "⚠️  ui/config.js not found, creating default config..."
  cat > ui/config.js << 'EOF'
window.CONFIG = {
  API_BASE: "", // same-origin in RunPod
  API_KEY: "", // optional API key
  LOG_POLL_MS: 1000,
  DEFAULT_CHECKPOINT: "checkpoint-13"
};
EOF
fi

# Ensure proper script loading order in HTML
if [ -f ui/index.html ]; then
  echo "🔧 Ensuring proper script loading order..."
  # Remove any existing script tags
  sed -i 's#<script src="config.js.*</script>##g' ui/index.html
  sed -i 's#<script src="app.js.*</script>##g' ui/index.html
  
  # Add scripts in correct order before closing body tag
  sed -i 's#</body>#    <script src="config.js?v=8"></script>\n    <script src="app.js?v=8"></script>\n  </body>#' ui/index.html
  echo "✅ Updated ui/index.html script loading"
fi

# Step 5 — stop any existing services on port 8888
echo "🛑 Step 5: Stopping existing services on port 8888..."
apt-get update -y >/dev/null 2>&1 && apt-get install -y psmisc >/dev/null 2>&1 || true
fuser -k 8888/tcp 2>/dev/null || true
pkill -f "jupyter.*8888" 2>/dev/null || true
pkill -f "uvicorn.*8888" 2>/dev/null || true
sleep 2

# Step 6 — start the API server
echo "🚀 Step 6: Starting API server..."
cd ~/mono_gen

# Create outputs directory if it doesn't exist
mkdir -p api/outputs

# Start the server
echo "Starting uvicorn with: $APP"
cd api
nohup uvicorn fastapi_app:app --host 0.0.0.0 --port 8888 --workers 1 --log-level info > ../server.log 2>&1 &
cd ..
sleep 3

# Show server startup logs
echo "📋 Server startup logs:"
tail -n 20 server.log

# Step 7 — API sanity check
echo "🔍 Step 7: Testing API..."
sleep 2

# Test health endpoint
echo "Testing health endpoint..."
if curl -s http://127.0.0.1:8888/healthz | grep -q '"ok": true'; then
  echo "✅ API is running successfully on port 8888!"
  echo "🌐 Your RunPod HTTP link should now show the mono_gen UI"
else
  echo "❌ API health check failed!"
  echo "Server logs:"
  tail -n 30 server.log
  echo ""
  echo "Trying to restart server..."
  pkill -f uvicorn
  sleep 2
  cd api
  nohup uvicorn fastapi_app:app --host 0.0.0.0 --port 8888 --workers 1 --log-level info > ../server.log 2>&1 &
  cd ..
  sleep 3
  tail -n 20 server.log
fi

# Step 8 — show final status
echo ""
echo "🎉 Setup complete!"
echo "📊 Server status:"
ps aux | grep uvicorn | grep -v grep || echo "⚠️  Server process not found"
echo ""
echo "🌐 Access your app via the RunPod HTTP link to port 8888"
echo "📝 Server logs: tail -f ~/mono_gen/server.log"
echo "🛑 Stop server: pkill -f uvicorn"
echo ""
echo "🧪 Test the API:"
echo "curl -s http://127.0.0.1:8888/healthz"
echo ""
echo "🎬 Test video generation:"
echo "curl -X POST http://127.0.0.1:8888/generate -H 'Content-Type: application/json' -d '{\"seconds\":2,\"fps\":8,\"out_res\":256}'"