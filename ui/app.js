// Configuration for backend endpoints
const APP_CONFIG = Object.assign({
  API_BASE: "", // same-origin by default
  API_KEY: "",
  DEFAULT_CHECKPOINT: "checkpoint-13",
  POLL_INTERVAL_MS: 2000, // Poll every 2 seconds
  POLL_TIMEOUT_MS: 10 * 60 * 1000, // 10 minute timeout
  LOG_POLL_MS: 1000
}, (window.CONFIG || {}));

function buildHeaders(extra = {}) {
  const headers = { ...extra };
  if (APP_CONFIG.API_KEY) {
    headers['X-API-Key'] = APP_CONFIG.API_KEY;
  }
  return headers;
}

// Helper to switch views (compatible with legacy markup)
function showView(id) {
  let found = false;
  document.querySelectorAll('.view').forEach(view => {
    if (!view) {
      return;
    }

    const isActive = view.id === id;
    if (isActive) {
      found = true;
    }

    view.classList.toggle('view--active', isActive);
    if (view.style) {
      view.style.display = isActive ? 'block' : 'none';
    }
  });

  if (!found) {
    console.warn('showView: requested view not found', id);
  }
}

// API helpers for new job-based system
async function initiateLatentWalk() {
  const url = `${APP_CONFIG.API_BASE}/generate`;
  const res = await fetch(url, {
    method: 'POST',
    headers: buildHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      seconds: 30,
      fps: 30,
      out_res: 512,
      anchors: 6,
      strength: 2.0,
      sharpen: false
    })
  });
  if (!res.ok) throw new Error(`initiate failed (${res.status})`);
  const data = await res.json();
  return { jobId: data.job_id };
}

async function getJobStatus(jobId) {
  const url = `${APP_CONFIG.API_BASE}/status/${jobId}`;
  const res = await fetch(url, {
    headers: buildHeaders(),
  });
  if (!res.ok) throw new Error(`status check failed (${res.status})`);
  return await res.json();
}

// UI bindings
const btnStart = document.getElementById('btn-start');
const back1 = document.getElementById('back-to-landing');
const back2 = document.getElementById('back-to-landing-2');
const statusText = document.getElementById('status-text');
const statusTime = document.getElementById('status-time');
const statusCheckpoint = document.getElementById('status-checkpoint');
const resultVideo = document.getElementById('result-video');
const consoleEl = document.getElementById('console');
const legacyProgressBar = document.getElementById('progress-bar');

function setStartDisabled(disabled) {
  if (btnStart) {
    btnStart.disabled = disabled;
  }
}

function setStartDisabled(disabled) {
  if (btnStart) {
    btnStart.disabled = disabled;
  }
}

// Debug logging
console.log('UI JavaScript loaded');
console.log('Button element:', btnStart);
console.log('APP_CONFIG:', APP_CONFIG);

let pollTimer = null;
let pollStartedAt = 0;
let currentJobId = null;
let generating = false;

if (btnStart) {
  btnStart.addEventListener('click', async () => {
    console.log('Button clicked!');
    // Prevent double submissions
    if (generating) {
      console.log('Already generating, ignoring click');
      return;
    }

    console.log('Starting generation...');
    generating = true;
    setStartDisabled(true);

    try {
      showView('step-progress');
      // Reset UI
      if (statusText) {
        statusText.textContent = 'queued ...';
      }
      if (statusCheckpoint) {
        statusCheckpoint.textContent = APP_CONFIG.DEFAULT_CHECKPOINT;
      }
      pollStartedAt = Date.now();
      if (statusTime) {
        statusTime.textContent = new Date(pollStartedAt).toISOString();
      }
      if (consoleEl) { consoleEl.hidden = false; consoleEl.textContent = 'initializing latent walk ...'; }

      // Start job
      const { jobId } = await initiateLatentWalk();
      currentJobId = jobId;

      // Start polling for status
      startStatusPolling(jobId);

    } catch (err) {
      console.error(err);
      if (consoleEl) { consoleEl.hidden = false; consoleEl.textContent += `\nERROR: ${String(err && err.message || err)}`; }
      showView('step-landing');
      generating = false;
      setStartDisabled(false);
    }
    // Note: generating and btnStart.disabled are handled in startStatusPolling callbacks
  });
} else {
  console.warn('Start button not found; check markup.');
}

function startStatusPolling(jobId) {
  clearInterval(pollTimer);
  
  pollTimer = setInterval(async () => {
    try {
      const status = await getJobStatus(jobId);
      updateProgress(status);
      
      if (status.state === 'done') {
        clearInterval(pollTimer);
        await handleJobComplete(status);
      } else if (status.state === 'error') {
        clearInterval(pollTimer);
        handleJobError(status);
      }
      
      // Check for timeout
      if (Date.now() - pollStartedAt > APP_CONFIG.POLL_TIMEOUT_MS) {
        clearInterval(pollTimer);
        throw new Error('Job timed out');
      }
      
    } catch (err) {
      console.error('Status polling error:', err);
      clearInterval(pollTimer);
      if (consoleEl) { consoleEl.hidden = false; consoleEl.textContent += `\nERROR: ${String(err && err.message || err)}`; }
      showView('step-landing');
      generating = false;
      setStartDisabled(false);
    }
  }, APP_CONFIG.POLL_INTERVAL_MS);
}

function updateProgress(status) {
  // Update status text
  if (statusText) {
    if (status.state === 'queued') {
      statusText.textContent = 'queued ...';
    } else if (status.state === 'running') {
      if (typeof status.frames_done === 'number' && typeof status.total_frames === 'number') {
        statusText.textContent = `generating ... ${status.frames_done}/${status.total_frames} frames`;
      } else {
        statusText.textContent = 'generating ...';
      }
    } else if (status.state === 'done') {
      statusText.textContent = 'complete!';
    } else if (status.state === 'error') {
      statusText.textContent = 'error occurred';
    }
  }

  const timestamp = status.updated_at || status.completed_at || status.started_at;
  if (statusTime && timestamp) {
    statusTime.textContent = timestamp;
  }

  if (statusCheckpoint && status.checkpoint) {
    statusCheckpoint.textContent = status.checkpoint;
  }

  // Update console with log tail
  if (consoleEl && status.log_tail && status.log_tail.length > 0) {
    consoleEl.textContent = status.log_tail.join('\n');
  }
}

async function handleJobComplete(status) {
  try {
    // Show completion status
    if (statusText) {
      statusText.textContent = 'complete!';
    }

    // Wait a moment then show preview
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Load video
    if (status.download_url && resultVideo) {
      const baseVideoUrl = status.download_url.startsWith('http') ?
        status.download_url :
        `${APP_CONFIG.API_BASE}${status.download_url}`;

      const videoUrlObj = new URL(baseVideoUrl, window.location.origin);
      if (APP_CONFIG.API_KEY) {
        videoUrlObj.searchParams.set('api_key', APP_CONFIG.API_KEY);
      }

      resultVideo.src = videoUrlObj.toString();
      resultVideo.load();
    }

    showView('step-preview');

  } catch (err) {
    console.error('Error handling job completion:', err);
    if (consoleEl) { consoleEl.hidden = false; consoleEl.textContent += `\nERROR: ${String(err && err.message || err)}`; }
    showView('step-landing');
  } finally {
    generating = false;
    setStartDisabled(false);
  }
}

function handleJobError(status) {
  console.error('Job failed:', status);
  if (consoleEl) { consoleEl.hidden = false; consoleEl.textContent += `\nERROR: Job failed`; }
  showView('step-landing');
  generating = false;
  setStartDisabled(false);
}

if (back1) {
  back1.addEventListener('click', (e) => { e.preventDefault(); abortAndHome(); });
}
if (back2) {
  back2.addEventListener('click', (e) => { e.preventDefault(); abortAndHome(); });
}

function abortAndHome() {
  clearInterval(pollTimer);
  showView('step-landing');
  generating = false;
  setStartDisabled(false);
  currentJobId = null;
}
