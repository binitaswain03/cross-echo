// CrossEcho Real-Time Webcam, YOLOv8 Inference, & Soundwave Visualizer

const video = document.getElementById('webcam-video');
const canvas = document.getElementById('detection-canvas');
const ctx = canvas.getContext('2d');
const hiddenCanvas = document.getElementById('hidden-capture-canvas');
const hiddenCtx = hiddenCanvas.getContext('2d');
const btnToggleCamera = document.getElementById('btn-toggle-camera');
const btnToggleDetection = document.getElementById('btn-toggle-detection');
const videoPlaceholder = document.getElementById('video-placeholder');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const valFps = document.getElementById('val-fps');
const valLatency = document.getElementById('val-latency');
const detectedCount = document.getElementById('detected-count');
const liveLogsContainer = document.getElementById('live-logs-container');
const noLogsMsg = document.getElementById('no-logs-msg');

// Spectrogram Wave Canvas
const soundwaveCanvas = document.getElementById('soundwave-canvas');
const waveCtx = soundwaveCanvas.getContext('2d');

let stream = null;
let isCameraOn = false;
let isDetecting = false;
let detectionLoopId = null;

// Metrics tracking
let lastFrameTime = performance.now();
let frameCount = 0;
let fpsInterval = setInterval(updateFpsMeter, 1000);
let activeDetections = []; // Shared list for the wave animation to read

function updateFpsMeter() {
    if (isDetecting) {
        valFps.textContent = frameCount;
        frameCount = 0;
    } else {
        valFps.textContent = '0';
    }
}

// ----------------- Soundwave Spectrogram Animation -----------------
let waveOffset = 0;
function animateSoundwave() {
    if (!soundwaveCanvas) return;
    
    // Set width and height dynamically matching element size
    if (soundwaveCanvas.width !== soundwaveCanvas.clientWidth) {
        soundwaveCanvas.width = soundwaveCanvas.clientWidth;
        soundwaveCanvas.height = 80;
    }
    
    const w = soundwaveCanvas.width;
    const h = soundwaveCanvas.height;
    
    waveCtx.fillStyle = '#020617';
    waveCtx.fillRect(0, 0, w, h);
    
    // Draw background grid lines on wave canvas
    waveCtx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
    waveCtx.lineWidth = 1;
    for (let x = 0; x < w; x += 30) {
        waveCtx.beginPath();
        waveCtx.moveTo(x, 0);
        waveCtx.lineTo(x, h);
        waveCtx.stroke();
    }
    waveCtx.beginPath();
    waveCtx.moveTo(0, h/2);
    waveCtx.lineTo(w, h/2);
    waveCtx.stroke();

    // Determine wave parameters based on detections
    let targetAmplitude = 2; // Flat static line if idle
    let targetFrequency = 0.02;
    let waveColor = '#475569'; // Muted slate gray
    
    if (isDetecting && activeDetections.length > 0) {
        // Active detections increase amplitude and alter wavelength
        targetAmplitude = 18;
        waveColor = '#06b6d4'; // Active cyan
        
        // Find highest confidence or first object to set pitch signature
        const primary = activeDetections[0];
        if (primary.label === 'person') {
            targetFrequency = 0.04;
            waveColor = '#06b6d4'; // Cyan
        } else if (primary.label === 'chair') {
            targetFrequency = 0.06;
            waveColor = '#f59e0b'; // Amber
        } else if (primary.label === 'car') {
            targetFrequency = 0.02;
            waveColor = '#d946ef'; // Fuchsia
        } else {
            targetFrequency = 0.03;
            waveColor = '#6366f1'; // Indigo
        }
    } else if (isCameraOn) {
        // Idle camera
        targetAmplitude = 4;
        waveColor = '#312e81'; // Deep dark blue
    }
    
    // Draw actual wave lines (composed of multiple sine layers)
    waveCtx.lineWidth = 2.5;
    waveCtx.shadowBlur = 10;
    waveCtx.shadowColor = waveColor;
    
    // Layer 1 (Main wave)
    waveCtx.strokeStyle = waveColor;
    waveCtx.beginPath();
    for (let x = 0; x < w; x++) {
        const y = h/2 + Math.sin(x * targetFrequency + waveOffset) * targetAmplitude;
        if (x === 0) waveCtx.moveTo(x, y);
        else waveCtx.lineTo(x, y);
    }
    waveCtx.stroke();
    
    // Layer 2 (Overlay wave, slightly out of phase)
    waveCtx.strokeStyle = waveColor + '77'; // Semi-transparent
    waveCtx.lineWidth = 1.5;
    waveCtx.beginPath();
    for (let x = 0; x < w; x++) {
        const y = h/2 + Math.sin(x * (targetFrequency * 1.5) - waveOffset) * (targetAmplitude * 0.7);
        if (x === 0) waveCtx.moveTo(x, y);
        else waveCtx.lineTo(x, y);
    }
    waveCtx.stroke();
    
    waveCtx.shadowBlur = 0; // Reset glow
    
    waveOffset += 0.15;
    requestAnimationFrame(animateSoundwave);
}

// Start soundwave loop
animateSoundwave();


// ----------------- Webcam Stream Controls -----------------

async function toggleCamera() {
    if (isCameraOn) {
        stopCamera();
    } else {
        await startCamera();
    }
}

async function startCamera() {
    btnToggleCamera.disabled = true;
    btnToggleCamera.querySelector('span').textContent = 'Acquiring drivers...';
    
    try {
        let constraints = {
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user'
            },
            audio: false
        };
        try {
            stream = await navigator.mediaDevices.getUserMedia(constraints);
        } catch (cErr) {
            stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        }
        
        video.srcObject = stream;
        
        await new Promise((resolve) => {
            if (video.readyState >= 1) {
                resolve();
            } else {
                video.onloadedmetadata = () => resolve();
                setTimeout(resolve, 800);
            }
        });
        
        try { await video.play(); } catch(pErr) {}

        isCameraOn = true;
        videoPlaceholder.style.display = 'none';
        btnToggleCamera.disabled = false;
        btnToggleCamera.querySelector('span').textContent = 'Close Camera Stream';
        btnToggleCamera.classList.replace('btn-secondary', 'btn-danger');
        btnToggleCamera.querySelector('i').setAttribute('data-lucide', 'video-off');
        btnToggleDetection.disabled = false;
        
        statusDot.style.backgroundColor = 'var(--color-success)';
        statusText.textContent = 'Camera Streaming';
        
        // Initial coordinate resolution bindings
        const w = video.videoWidth || 640;
        const h = video.videoHeight || 480;
        canvas.width = w;
        canvas.height = h;
        hiddenCanvas.width = w;
        hiddenCanvas.height = h;
        
        lucide.createIcons();
        printTerminalLine('system', 'Webcam stream established successfully.');
    } catch (err) {
        console.error('Error opening camera: ', err);
        isCameraOn = false;
        btnToggleCamera.disabled = false;
        btnToggleCamera.querySelector('span').textContent = 'Start Camera Stream';
        printTerminalLine('error', 'Failed to connect video drivers: ' + err.message);
    }
}

function stopCamera() {
    if (isDetecting) {
        stopDetection();
    }
    
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    
    video.srcObject = null;
    isCameraOn = false;
    videoPlaceholder.style.display = 'flex';
    btnToggleCamera.querySelector('span').textContent = 'Start Camera Stream';
    btnToggleCamera.classList.replace('btn-danger', 'btn-secondary');
    btnToggleCamera.querySelector('i').setAttribute('data-lucide', 'video');
    btnToggleDetection.disabled = true;
    
    statusDot.style.backgroundColor = 'var(--color-danger)';
    statusText.textContent = 'System Standby';
    
    // Clear canvas overlay
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    activeDetections = [];
    
    lucide.createIcons();
    printTerminalLine('system', 'Webcam stream closed by operator.');
}

// ----------------- AI Detection Controls -----------------

function toggleDetection() {
    if (isDetecting) {
        stopDetection();
    } else {
        startDetection();
    }
}

function startDetection() {
    isDetecting = true;
    btnToggleDetection.querySelector('span').textContent = 'Terminate Inference';
    btnToggleDetection.classList.replace('btn-cyan', 'btn-secondary');
    btnToggleDetection.querySelector('i').setAttribute('data-lucide', 'square');
    
    statusDot.style.backgroundColor = 'var(--color-accent)';
    statusText.textContent = 'Analyzing Frames...';
    
    printTerminalLine('system', 'YOLOv8 inference engine initialized.');
    runDetectionLoop();
    lucide.createIcons();
}

function stopDetection() {
    isDetecting = false;
    if (detectionLoopId) {
        clearTimeout(detectionLoopId);
        detectionLoopId = null;
    }
    
    btnToggleDetection.querySelector('span').textContent = 'Initialize Inference';
    btnToggleDetection.classList.replace('btn-secondary', 'btn-cyan');
    btnToggleDetection.querySelector('i').setAttribute('data-lucide', 'cpu');
    
    if (isCameraOn) {
        statusDot.style.backgroundColor = 'var(--color-success)';
        statusText.textContent = 'Camera Streaming';
    }
    
    detectedCount.textContent = '0';
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    activeDetections = [];
    valLatency.textContent = '0ms';
    
    printTerminalLine('system', 'YOLOv8 inference engine terminated.');
    lucide.createIcons();
}

// ----------------- Core Inference Loop -----------------

async function runDetectionLoop() {
    if (!isDetecting || !isCameraOn) return;
    
    const startTime = performance.now();
    
    // Safety check for dynamic resolution changes
    const w = video.videoWidth || 640;
    const h = video.videoHeight || 480;
    if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
        hiddenCanvas.width = w;
        hiddenCanvas.height = h;
    }

    try {
        // Draw frame to hidden canvas
        hiddenCtx.drawImage(video, 0, 0, hiddenCanvas.width, hiddenCanvas.height);
        
        // Export frame
        const frameDataUrl = hiddenCanvas.toDataURL('image/jpeg', 0.65);
        
        const response = await fetch('/api/detect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image: frameDataUrl })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success && isDetecting) {
                const latency = Math.round(performance.now() - startTime);
                valLatency.textContent = `${latency}ms`;
                
                activeDetections = data.detections;
                detectedCount.textContent = data.count;
                
                // Draw boxes
                drawBoundingBoxes(data.detections);
                
                // Log detections in the custom terminal
                logDetectionsToTerminal(data.detections);
                
                frameCount++;
            }
        }
    } catch (err) {
        console.error('Frame inference error: ', err);
    }
    
    // Schedule next frame capture loop (150ms delay)
    if (isDetecting) {
        detectionLoopId = setTimeout(runDetectionLoop, 150);
    }
}

// Draw futuristic HUD styled bounding boxes
function drawBoundingBoxes(detections) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    detections.forEach(det => {
        const [x1, y1, x2, y2] = det.box;
        const width = x2 - x1;
        const height = y2 - y1;
        
        // Pick class coloring matching simulator
        let color = '#6366f1'; // Default Indigo
        if (det.label === 'person') color = '#06b6d4'; // Cyan
        else if (det.label === 'chair') color = '#f59e0b'; // Amber
        else if (det.label === 'car') color = '#d946ef'; // Fuchsia
        else if (det.label === 'mobile phone') color = '#10b981'; // Emerald
        
        // Draw box border with glowing properties
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.shadowColor = color;
        ctx.shadowBlur = 8;
        
        // Rounded bounding rectangle
        ctx.strokeRect(x1, y1, width, height);
        
        // Draw label pill background
        ctx.shadowBlur = 0; // Disable blur for text card
        ctx.fillStyle = color;
        const tagText = `${det.label.toUpperCase()} [${det.confidence}%]`;
        ctx.font = 'bold 11px monospace';
        const textW = ctx.measureText(tagText).width;
        
        ctx.fillRect(x1 - 1.5, y1 - 20, textW + 12, 20);
        
        // Draw tag text
        ctx.fillStyle = '#ffffff';
        ctx.fillText(tagText, x1 + 5, y1 - 6);
    });
}

// ----------------- Terminal Log Feed Helpers -----------------

function printTerminalLine(type, text) {
    if (noLogsMsg) {
        noLogsMsg.style.display = 'none';
    }
    
    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour12: false });
    
    const line = document.createElement('div');
    line.className = 'terminal-line';
    
    let colorClass = 'terminal-success';
    let prefix = '[SQLITE]';
    
    if (type === 'system') {
        colorClass = 'terminal-prompt';
        prefix = '[SYSTEM]';
    } else if (type === 'error') {
        colorClass = 'terminal-danger';
        prefix = '[CRITICAL]';
    }
    
    line.innerHTML = `
        <span style="color: var(--text-dark);">${timeStr}</span> 
        <span class="${colorClass}" style="font-weight:600;">${prefix}</span> 
        ${text}
    `;
    
    liveLogsContainer.insertBefore(line, liveLogsContainer.firstChild);
    
    // Cap DOM children count to 30
    while (liveLogsContainer.children.length > 30) {
        liveLogsContainer.removeChild(liveLogsContainer.lastChild);
    }
}

function logDetectionsToTerminal(detections) {
    if (detections.length === 0) return;
    
    detections.forEach(det => {
        // To avoid flooding the log, only show log items with a 5-second in-memory print cooldown
        // (This mirrors the server-side DB logging cooldown to represent DB transactions accurately)
        const cooldownKey = 'logged_' + det.label;
        const now = Date.now();
        const lastPrinted = window[cooldownKey] || 0;
        
        if (now - lastPrinted >= 5000) {
            printTerminalLine('sqlite', `Recorded object <strong style="color:#fff; text-transform:capitalize;">${det.label}</strong> (accuracy: ${det.confidence}%) to DB tables.`);
            window[cooldownKey] = now;
        }
    });
}

// Clean handlers
window.addEventListener('beforeunload', () => {
    stopCamera();
    clearInterval(fpsInterval);
});
