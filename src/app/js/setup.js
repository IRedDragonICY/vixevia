import ModelController from './model.js';

const app = new PIXI.Application({
    view: document.getElementById("canvas"),
    autoStart: true,
    resizeTo: window
});
const modelController = new ModelController(app, "../model/live2d/vixevia.model3.json");
await modelController.loadModel();
modelController.startBlinking();
const statusDiv = document.getElementById('status');
let isProcessing = false;
let chunks = [];
const audioLink = "/temp/response.wav";
let audioPlaying = false;
let audio;
let currentStream;
const preview = document.getElementById('cameraPreview');
const cameraSelect = document.getElementById('cameraSelect');

function stopCurrentStream() {
    if (currentStream && currentStream.getTracks) {
        currentStream.getTracks().forEach(track => track.stop());
    }
}

async function startStream(deviceId) {
    stopCurrentStream();
    currentStream = await navigator.mediaDevices.getUserMedia({
        video: deviceId ? { deviceId: { exact: deviceId } } : true,
        audio: true
    });
    preview.srcObject = currentStream;
    const videoElement = document.createElement('video');
    videoElement.srcObject = currentStream;
    videoElement.autoplay = true;
    videoElement.muted = true;
    videoElement.addEventListener('playing', () => {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        const captureFrame = () => {
            if (videoElement.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
                canvas.width = videoElement.videoWidth;
                canvas.height = videoElement.videoHeight;
                context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
                canvas.toBlob(blob => {
                    if (blob) {
                        const formData = new FormData();
                        formData.append('image', blob, 'frame.jpg');
                        fetch('/api/upload_frame', { method: 'POST', body: formData });
                    }
                }, 'image/jpeg');
            }
            setTimeout(captureFrame, 2500);
        };
        captureFrame();
    });
    videoElement.play();
    const mediaRecorder = new MediaRecorder(currentStream);
    mediaRecorder.ondataavailable = e => chunks.push(e.data);
    mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/wav' });
        chunks = [];
        const formData = new FormData();
        formData.append('audio', blob, 'audio.wav');
        fetch('/api/upload_audio', { method: 'POST', body: formData })
            .then(() => {
                statusDiv.textContent = "";
                isProcessing = false;
                checkAudioReady();
            });
    };
    try {
        const MicVAD = window.vad.MicVAD;
        if (!MicVAD) throw new Error('MicVAD is not available');
        const micVAD = await MicVAD.new({
            onSpeechStart: () => {
                if (audioPlaying) {
                    audio.pause();
                    audio.currentTime = 0;
                    audioPlaying = false;
                }
                if (!isProcessing && mediaRecorder.state !== 'recording') {
                    mediaRecorder.start();
                    statusDiv.textContent = "Listening...";
                }
            },
            onSpeechEnd: () => {
                if (mediaRecorder.state === 'recording') {
                    mediaRecorder.stop();
                    isProcessing = true;
                    statusDiv.textContent = "Processing...";
                }
            }
        });
        if (typeof micVAD.start === 'function') {
            micVAD.start();
        }
    } catch (error) {
        console.error('Error initializing MicVAD:', error);
    }
}

function checkAudioReady() {
    const interval = setInterval(async () => {
        const response = await fetch('/api/audio_status');
        const data = await response.json();
        if (data.audio_ready) {
            clearInterval(interval);
            playBotAudio();
        }
    }, 500);
}

function playBotAudio() {
    audioPlaying = true;
    audio = new Audio(audioLink);
    audio.addEventListener('ended', () => {
        audioPlaying = false;
    });
    audio.play().then(() => {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const analyser = audioCtx.createAnalyser();
        const source = audioCtx.createMediaElementSource(audio);
        source.connect(analyser);
        analyser.connect(audioCtx.destination);
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        const analyseVolume = () => {
            analyser.getByteFrequencyData(dataArray);
            modelController.setMouthOpenY(
                dataArray.reduce((a, b) => a + b, 0) / dataArray.length / 255
            );
            if (!audio.paused) requestAnimationFrame(analyseVolume);
        };
        analyseVolume();
    });
}

const devices = await navigator.mediaDevices.enumerateDevices();
const videoDevices = devices.filter(d => d.kind === 'videoinput');
videoDevices.forEach(d => {
    const option = document.createElement('option');
    option.value = d.deviceId;
    option.text = d.label || `Camera ${cameraSelect.length + 1}`;
    cameraSelect.appendChild(option);
});
cameraSelect.addEventListener('change', () => {
    startStream(cameraSelect.value);
});

if (videoDevices.length > 0) {
    startStream(videoDevices[0].deviceId);
}
