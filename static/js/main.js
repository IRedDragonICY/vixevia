import { loadModel, startBlinking, setMouthOpenY } from './model.js';

export const app = new PIXI.Application({ view: document.getElementById("canvas"), autoStart: true, resizeTo: window });
const audio_link = "/temp/response.wav";
const statusDiv = document.getElementById('status');

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.continuous = false;
recognition.interimResults = false;

let model, video, audioPlaying = false, isProcessing = false, audioLoopRunning = false, mediaRecorder, chunks = [];

(async () => {
    [model] = await Promise.all([loadModel()]);
    startBlinking();
    setupVideo();
    setupAudio();
    initiateAudioPlay();
})();

function setupVideo() {
    video = document.createElement('video');
    video.autoplay = true;
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
            video.addEventListener('canplaythrough', () => requestAnimationFrame(captureFrame));
        })
        .catch(console.error);
}

function captureFrame() {
    if (video.readyState === 4) {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(blob => blob && sendFrameToServer(blob), 'image/jpeg');
    }
    setTimeout(() => requestAnimationFrame(captureFrame), 1000);
}

function sendFrameToServer(blob) {
    const formData = new FormData();
    formData.append('image', blob, 'frame.jpg');

    const sendRequest = (retryCount = 0) => {
        fetch('/api/upload_frame', { method: 'POST', body: formData })
            .then(response => console.log('Frame uploaded:', response))
            .catch(error => {
                console.error('Failed to upload frame:', error);
                if (retryCount < 3) {
                    setTimeout(() => sendRequest(retryCount + 1), 2000);
                }
            });
    };

    sendRequest();
}

async function initiateAudioPlay() {
    if (!audioPlaying && !audioLoopRunning) playAudioWhenReady();
}

async function playAudioWhenReady() {
    audioLoopRunning = true;
    while (!(await checkAudioStatus())) {
        await new Promise(resolve => setTimeout(resolve, 500)); // Reduce wait time
    }
    audioPlaying = true;
    const audio = new Audio(audio_link);
    await audio.play();
    setupAnalyser(audio);
    audioLoopRunning = false;
}

async function checkAudioStatus() {
    const response = await fetch('/api/audio_status');
    const data = await response.json();
    return data.audio_ready;
}

function setupAnalyser(audio) {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioCtx.createAnalyser();
    const source = audioCtx.createMediaElementSource(audio);
    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    source.connect(analyser);
    analyser.connect(audioCtx.destination);
    analyseVolume(analyser, dataArray, audio);

    audio.onended = async () => {
        await fetch('/api/reset_audio_status', { method: 'POST' });
        audioPlaying = false;
        if (!isProcessing) recognition.start();
    };
}

function analyseVolume(analyser, dataArray, audio) {
    analyser.getByteFrequencyData(dataArray);
    const volume = dataArray.reduce((prev, curr) => prev + curr, 0) / dataArray.length / 255;
    setMouthOpenY(volume);
    if (!audio.paused) requestAnimationFrame(() => analyseVolume(analyser, dataArray, audio));
}

function setupAudio() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = event => chunks.push(event.data);
            mediaRecorder.onstop = () => {
                const blob = new Blob(chunks, { type: 'audio/wav' });
                sendAudioToServer(blob);
                chunks = [];
            };
            setupVAD(stream);
        })
        .catch(console.error);
}

function sendAudioToServer(blob) {
    const formData = new FormData();
    formData.append('audio', blob, 'audio.wav');
    fetch('/api/upload_audio', { method: 'POST', body: formData })
        .then(response => {
            console.log('Audio uploaded:', response);
            statusDiv.innerHTML = "";
            isProcessing = false;
            initiateAudioPlay();
        })
        .catch(console.error);
}

async function setupVAD(stream) {
    const myvad = await vad.MicVAD.new({
        onSpeechStart: () => {
            if (isProcessing || audioPlaying) return;
            console.log("Speech start detected");
            statusDiv.innerHTML = "Listening...";
            mediaRecorder.start();
        },
        onSpeechEnd: () => {
            if (isProcessing || audioPlaying) return;
            console.log("Speech end detected");
            statusDiv.innerHTML = "Processing...";
            mediaRecorder.stop();
            isProcessing = true;
        }
    });
    myvad.start();
}
