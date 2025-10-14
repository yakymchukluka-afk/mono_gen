// Configuration for backend endpoints
const APP_CONFIG = Object.assign({
  API_BASE: "", // same-origin by default
  DEFAULT_CHECKPOINT: "checkpoint-13",
  POLL_INTERVAL_MS: 1500,
  POLL_TIMEOUT_MS: 5 * 60 * 1000,
  LOG_POLL_MS: 1000
}, (window.config || {}));

// Helper to switch views
function showView(id) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('view--active'));
  document.getElementById(id).classList.add('view--active');
}

// API helpers — adjust mapping if your backend differs
async function initiateLatentWalk(checkpoint) {
  const url = `${APP_CONFIG.API_BASE}/generate`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      seconds: 2,
      fps: 8,
      out_res: 256,
      anchors: 3,
      strength: 2.0,
      sharpen: false,
      checkpoint: checkpoint
    })
  });
  if (!res.ok) throw new Error(`initiate failed (${res.status})`);
  return parseInitiateResponse(await res.json());
}

function parseInitiateResponse(json) {
  // Expect: { video_path, download_url }
  return { videoPath: json.video_path, downloadUrl: json.download_url };
}

// Logs
async function fetchLogsTail(tail) {
  const url = `${APP_CONFIG.API_BASE}/logs?tail=${encodeURIComponent(tail || 200)}`;
  const res = await fetch(url, { headers: { 'Accept': 'text/plain' } });
  if (!res.ok) return '';
  return await res.text();
}

// UI bindings
const btnStart = document.getElementById('btn-start');
const back1 = document.getElementById('back-to-landing');
const back2 = document.getElementById('back-to-landing-2');
const progressBar = document.getElementById('progress-bar');
const statusText = document.getElementById('status-text');
const statusTime = document.getElementById('status-time');
const statusCheckpoint = document.getElementById('status-checkpoint');
const resultVideo = document.getElementById('result-video');
const consoleEl = document.getElementById('console');

let pollTimer = null;
let pollStartedAt = 0;
let logTimer = null;

btnStart.addEventListener('click', async () => {
  try {
    showView('step-progress');
    // Reset UI
    progressBar.style.width = '0%';
    statusText.textContent = 'producing ...';
    statusCheckpoint.textContent = APP_CONFIG.DEFAULT_CHECKPOINT;
    pollStartedAt = Date.now();
    statusTime.textContent = new Date(pollStartedAt).toISOString();
    if (consoleEl) { consoleEl.hidden = false; consoleEl.textContent = ''; }

    startLogPolling();
    const { downloadUrl } = await initiateLatentWalk(APP_CONFIG.DEFAULT_CHECKPOINT);
    // we no longer poll a status endpoint; we will fetch the video with retries
    await fetchVideoWithRetry(downloadUrl, 10000);
    showView('step-preview');
  } catch (err) {
    console.error(err);
    if (consoleEl) { consoleEl.hidden = false; consoleEl.textContent += `\nERROR: ${String(err && err.message || err)}`; }
    showView('step-landing');
  }
});

function startLogPolling() {
  if (!consoleEl) return;
  if (!APP_CONFIG.LOG_POLL_MS || APP_CONFIG.LOG_POLL_MS <= 0) return;
  clearInterval(logTimer);
  logTimer = setInterval(async () => {
    try {
      const txt = await fetchLogsTail(200);
      if (typeof txt === 'string') consoleEl.textContent = txt.trim();
    } catch {}
  }, APP_CONFIG.LOG_POLL_MS);
}

async function fetchVideoWithRetry(downloadUrl, timeoutMs) {
  const started = Date.now();
  const url = downloadUrl.startsWith('http') ? downloadUrl : `${APP_CONFIG.API_BASE}${downloadUrl}`;
  let delay = 250;
  while (true) {
    try {
      const res = await fetch(url);
      if (res.ok) {
        const blob = await res.blob();
        const objectUrl = URL.createObjectURL(blob);
        resultVideo.src = objectUrl;
        resultVideo.load();
        clearInterval(logTimer);
        return;
      }
    } catch {}
    if (Date.now() - started > (timeoutMs || 10000)) {
      clearInterval(logTimer);
      throw new Error('Download not available after retry window');
    }
    await new Promise(r => setTimeout(r, delay));
    delay = Math.min(2000, delay + 250);
  }
}

back1.addEventListener('click', (e) => { e.preventDefault(); abortAndHome(); });
back2.addEventListener('click', (e) => { e.preventDefault(); abortAndHome(); });

function abortAndHome() {
  clearInterval(pollTimer);
  clearInterval(logTimer);
  showView('step-landing');
}


