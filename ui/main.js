// Configuration - will be loaded from config.js
let config = {
    API_BASE: "https://your-runpod-host:8888",
    API_KEY: ""
};

// Load configuration
async function loadConfig() {
    try {
        const response = await fetch('./config.js');
        const text = await response.text();
        // Extract config from the loaded script
        const configMatch = text.match(/window\.config\s*=\s*({[\s\S]*?});/);
        if (configMatch) {
            config = JSON.parse(configMatch[1]);
        }
    } catch (error) {
        console.warn('Could not load config.js, using defaults');
    }
}

// DOM elements
const step1 = document.getElementById('step1');
const step2 = document.getElementById('step2');
const errorMessage = document.getElementById('errorMessage');
const generateBtn = document.getElementById('generateBtn');
const previewVideo = document.getElementById('previewVideo');
const videoSource = document.getElementById('videoSource');
const downloadLink = document.getElementById('downloadLink');
const newVideoBtn = document.getElementById('newVideoBtn');
const retryBtn = document.getElementById('retryBtn');

// Form controls
const secondsInput = document.getElementById('seconds');
const fpsInput = document.getElementById('fps');
const resolutionSelect = document.getElementById('resolution');

// State
let currentVideoPath = null;
let currentJobId = null;
let statusCheckInterval = null;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadConfig();
    setupEventListeners();
});

function setupEventListeners() {
    generateBtn.addEventListener('click', generateVideo);
    newVideoBtn.addEventListener('click', showStep1);
    retryBtn.addEventListener('click', showStep1);
}

async function generateVideo() {
    try {
        // Show loading state
        setLoading(true);
        hideError();
        
        // Get form values
        const seconds = parseInt(secondsInput.value);
        const fps = parseInt(fpsInput.value);
        const resolution = parseInt(resolutionSelect.value);
        
        // Validate inputs
        if (seconds < 5 || seconds > 120) {
            throw new Error('Duration must be between 5 and 120 seconds');
        }
        if (fps < 10 || fps > 60) {
            throw new Error('FPS must be between 10 and 60');
        }
        
        // Prepare request
        const requestBody = {
            seconds: seconds,
            fps: fps,
            out_res: resolution,
            anchors: 6,
            strength: 2.0,
            sharpen: true
        };
        
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // Add API key if configured
        if (config.API_KEY) {
            headers['X-API-Key'] = config.API_KEY;
        }
        
        // Start video generation
        const response = await fetch(`${config.API_BASE}/generate`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        currentJobId = data.job_id;
        
        // Start polling for status
        startStatusPolling();
        
    } catch (error) {
        console.error('Generation failed:', error);
        showError(error.message);
        setLoading(false);
    }
}

function startStatusPolling() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    statusCheckInterval = setInterval(async () => {
        try {
            await checkJobStatus();
        } catch (error) {
            console.error('Status check failed:', error);
            stopStatusPolling();
            showError('Failed to check generation status');
            setLoading(false);
        }
    }, 2000); // Check every 2 seconds
}

function stopStatusPolling() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }
}

async function checkJobStatus() {
    if (!currentJobId) return;
    
    const headers = {};
    if (config.API_KEY) {
        headers['X-API-Key'] = config.API_KEY;
    }
    
    const response = await fetch(`${config.API_BASE}/status/${currentJobId}`, {
        headers: headers
    });
    
    if (!response.ok) {
        throw new Error(`Status check failed: ${response.status}`);
    }
    
    const status = await response.json();
    
    if (status.status === 'completed') {
        stopStatusPolling();
        currentVideoPath = status.download_url;
        showVideoPreview(status.download_url);
        setLoading(false);
    } else if (status.status === 'error') {
        stopStatusPolling();
        showError(status.error || 'Video generation failed');
        setLoading(false);
    } else if (status.status === 'processing') {
        setLoading(true, 'Generating video...');
    } else if (status.status === 'queued') {
        setLoading(true, 'Queued for generation...');
    }
    // Continue polling for queued/processing status
}

function showVideoPreview(downloadUrl) {
    // Set video source
    const fullVideoUrl = `${config.API_BASE}${downloadUrl}`;
    videoSource.src = fullVideoUrl;
    previewVideo.load();
    
    // Set download link
    downloadLink.href = fullVideoUrl;
    downloadLink.download = `latent_walk_${secondsInput.value}s_${fpsInput.value}fps.mp4`;
    
    // Show step 2
    step1.classList.remove('active');
    step2.classList.add('active');
}

function showStep1() {
    stopStatusPolling();
    step2.classList.remove('active');
    step1.classList.add('active');
    hideError();
    currentJobId = null;
    currentVideoPath = null;
}

function setLoading(loading, message = 'Generating...') {
    generateBtn.disabled = loading;
    generateBtn.classList.toggle('loading', loading);
    
    if (loading) {
        const loadingText = generateBtn.querySelector('.loading-text');
        if (loadingText) {
            loadingText.textContent = message;
        }
    }
}

function showError(message) {
    document.getElementById('errorText').textContent = message;
    errorMessage.style.display = 'block';
    step1.classList.add('active');
    step2.classList.remove('active');
}

function hideError() {
    errorMessage.style.display = 'none';
}

// Handle video load errors
previewVideo.addEventListener('error', () => {
    showError('Failed to load video. Please try again.');
});

// Handle download errors
downloadLink.addEventListener('click', (e) => {
    if (!currentVideoPath) {
        e.preventDefault();
        showError('No video available for download');
    }
});