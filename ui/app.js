// Configuration for backend endpoints
const APP_CONFIG = Object.assign({
  API_BASE: "", // same-origin by default
  DEFAULT_CHECKPOINT: "checkpoint-13",
  POLL_INTERVAL_MS: 2000, // Poll every 2 seconds
  POLL_TIMEOUT_MS: 10 * 60 * 1000, // 10 minute timeout
  LOG_POLL_MS: 1000
}, (window.CONFIG || {}));

// Helper to switch views
function showView(id) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('view--active'));
  document.getElementById(id).classList.add('view--active');
}

// API helpers for new job-based system
async function initiateLatentWalk() {
  const url = `${APP_CONFIG.API_BASE}/generate`;
  const headers = { 'Content-Type': 'application/json' };
  
  // Add API key if configured
  if (APP_CONFIG.API_KEY) {
    headers['X-API-Key'] = APP_CONFIG.API_KEY;
  }
  
  const res = await fetch(url, {
    method: 'POST',
    headers: headers,
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
  const headers = {};
  
  // Add API key if configured
  if (APP_CONFIG.API_KEY) {
    headers['X-API-Key'] = APP_CONFIG.API_KEY;
  }
  
  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error(`status check failed (${res.status})`);
  return await res.json();
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

// Debug logging
console.log('UI JavaScript loaded');
console.log('Button element:', btnStart);
console.log('APP_CONFIG:', APP_CONFIG);

let pollTimer = null;
let pollStartedAt = 0;
let currentJobId = null;
let generating = false;

btnStart.addEventListener('click', async () => {
  console.log('Button clicked!');
  // Prevent double submissions
  if (generating) {
    console.log('Already generating, ignoring click');
    return;
  }
  
  console.log('Starting generation...');
  generating = true;
  btnStart.disabled = true;
  
  try {
    showView('step-progress');
    // Reset UI
    progressBar.style.width = '0%';
    statusText.textContent = 'queued ...';
    statusCheckpoint.textContent = APP_CONFIG.DEFAULT_CHECKPOINT;
    pollStartedAt = Date.now();
    statusTime.textContent = new Date(pollStartedAt).toISOString();
    if (consoleEl) { consoleEl.hidden = false; consoleEl.textContent = ''; }

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
    btnStart.disabled = false;
  }
  // Note: generating and btnStart.disabled are handled in startStatusPolling callbacks
});

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
      btnStart.disabled = false;
    }
  }, APP_CONFIG.POLL_INTERVAL_MS);
}

function updateProgress(status) {
  // Update progress bar
  const progressPercent = Math.round(status.progress * 100);
  progressBar.style.width = `${progressPercent}%`;
  
  // Update status text
  if (status.state === 'queued') {
    statusText.textContent = 'queued ...';
  } else if (status.state === 'running') {
    statusText.textContent = `generating ... ${status.frames_done}/${status.total_frames} frames`;
  } else if (status.state === 'done') {
    statusText.textContent = 'complete!';
  } else if (status.state === 'error') {
    statusText.textContent = 'error occurred';
  }
  
  // Update console with log tail
  if (consoleEl && status.log_tail && status.log_tail.length > 0) {
    consoleEl.textContent = status.log_tail.join('\n');
  }
}

async function handleJobComplete(status) {
  try {
    // Show completion status
    statusText.textContent = 'complete!';
    progressBar.style.width = '100%';
    
    // Wait a moment then show preview
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Load video
    if (status.download_url) {
      const videoUrl = status.download_url.startsWith('http') ? 
        status.download_url : 
        `${APP_CONFIG.API_BASE}${status.download_url}`;
      
      resultVideo.src = videoUrl;
      resultVideo.load();
    }
    
    showView('step-preview');
    
  } catch (err) {
    console.error('Error handling job completion:', err);
    if (consoleEl) { consoleEl.hidden = false; consoleEl.textContent += `\nERROR: ${String(err && err.message || err)}`; }
    showView('step-landing');
  } finally {
    generating = false;
    btnStart.disabled = false;
  }
}

function handleJobError(status) {
  console.error('Job failed:', status);
  if (consoleEl) { consoleEl.hidden = false; consoleEl.textContent += `\nERROR: Job failed`; }
  showView('step-landing');
  generating = false;
  btnStart.disabled = false;
}

back1.addEventListener('click', (e) => { e.preventDefault(); abortAndHome(); });
back2.addEventListener('click', (e) => { e.preventDefault(); abortAndHome(); });

function abortAndHome() {
  clearInterval(pollTimer);
  showView('step-landing');
  generating = false;
  btnStart.disabled = false;
  currentJobId = null;
}