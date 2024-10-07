import ModelController from './model.js';

const app = new PIXI.Application({ view: document.getElementById("canvas"), autoStart: true, resizeTo: window });
const modelPath = "../model/live2d/vixevia.model3.json";
const audioLink = "/temp/response.wav";
const statusDiv = document.getElementById('status');
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.continuous = false;
recognition.interimResults = false;

let modelController, video, audioPlaying = false, isProcessing = false, mediaRecorder, chunks = [];

(async () => {
    modelController = new ModelController(app, modelPath);
    await modelController.loadModel();
    modelController.startBlinking();
    setupMedia();
})();

function setupMedia() {
    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        .then(stream => {
            setupVideo(stream);
            setupAudio(stream);
        })
        .catch(console.error);
}

function setupVideo(stream) {
    video = document.createElement('video');
    video.srcObject = stream;
    video.autoplay = true;
    video.addEventListener('canplay', () => requestAnimationFrame(captureFrame));
}

function captureFrame() {
    if (video.readyState === 4) {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(blob => blob && sendFrameToServer(blob), 'image/jpeg');
    }
    setTimeout(() => requestAnimationFrame(captureFrame), 2500);
}

function sendFrameToServer(blob) {
    const formData = new FormData();
    formData.append('image', blob, 'frame.jpg');
    fetch('/api/upload_frame', { method: 'POST', body: formData }).catch(console.error);
}

function setupAudio(stream) {
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = event => chunks.push(event.data);
    mediaRecorder.onstop = () => processAudio();

    const vad = vad.MicVAD.new({
        onSpeechStart: () => startRecording(),
        onSpeechEnd: () => stopRecording(),
    });

    vad.start();
}

function startRecording() {
    if (!isProcessing && !audioPlaying) {
        mediaRecorder.start();
        statusDiv.innerHTML = "Listening...";
    }
}

function stopRecording() {
    if (!isProcessing && !audioPlaying) {
        mediaRecorder.stop();
        isProcessing = true;
        statusDiv.innerHTML = "Processing...";
    }
}

function processAudio() {
    const blob = new Blob(chunks, { type: 'audio/wav' });
    sendAudioToServer(blob);
    chunks = [];
}

function sendAudioToServer(blob) {
    const formData = new FormData();
    formData.append('audio', blob, 'audio.wav');
    fetch('/api/upload_audio', { method: 'POST', body: formData })
        .then(() => {
            statusDiv.innerHTML = "";
            isProcessing = false;
            playAudioWhenReady();
        })
        .catch(console.error);
}

async function playAudioWhenReady() {
    while (!(await checkAudioStatus())) {
        await new Promise(resolve => setTimeout(resolve, 500));
    }
    audioPlaying = true;
    const audio = new Audio(audioLink);
    audio.play().then(() => setupAnalyser(audio));
}

async function checkAudioStatus() {
    try {
        const response = await fetch('/api/audio_status');
        const data = await response.json();
        return data.audio_ready;
    } catch (error) {
        console.error('Failed to check audio status:', error);
        return false;
    }
}

function setupAnalyser(audio) {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioCtx.createAnalyser();
    const source = audioCtx.createMediaElementSource(audio);
    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    source.connect(analyser);
    analyser.connect(audioCtx.destination);

    function analyseVolume() {
        analyser.getByteFrequencyData(dataArray);
        const volume = dataArray.reduce((acc, val) => acc + val, 0) / dataArray.length / 255;
        modelController.setMouthOpenY(volume);
        if (!audio.paused) requestAnimationFrame(analyseVolume);
    }

    analyseVolume();
    audio.onended = resetAudioState;
}

function resetAudioState() {
    fetch('/api/reset_audio_status', { method: 'POST' });
    audioPlaying = false;
    if (!isProcessing) recognition.start();
}
