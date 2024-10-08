import ModelController from './model.js';

(async () => {
    const app = new PIXI.Application({
        view: document.getElementById("canvas"),
        autoStart: true,
        resizeTo: window
    });
    const modelController = new ModelController(app, "../model/live2d/vixevia.model3.json");
    await modelController.loadModel();
    modelController.startBlinking();

    const statusDiv = document.getElementById('status');
    const audioLink = "/temp/response.wav";
    let audioPlaying = false;
    let isProcessing = false;
    let chunks = [];

    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    const video = document.createElement('video');
    video.srcObject = stream;
    video.autoplay = true;
    video.addEventListener('canplay', () => {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        (function captureFrame() {
            if (video.readyState === 4) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
                canvas.toBlob(blob => blob && fetch('/api/upload_frame', {
                    method: 'POST',
                    body: new FormData().append('image', blob, 'frame.jpg')
                }), 'image/jpeg');
            }
            setTimeout(captureFrame, 2500);
        })();
    });

    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.addEventListener('dataavailable', e => chunks.push(e.data));
    mediaRecorder.addEventListener('stop', () => {
        const blob = new Blob(chunks, { type: 'audio/wav' });
        chunks = [];
        fetch('/api/upload_audio', {
            method: 'POST',
            body: new FormData().append('audio', blob, 'audio.wav')
        }).then(() => {
            statusDiv.textContent = "";
            isProcessing = false;
            (async function playAudioWhenReady() {
                while (!(await fetch('/api/audio_status').then(res => res.json()).then(data => data.audio_ready))) {
                    await new Promise(r => setTimeout(r, 500));
                }
                audioPlaying = true;
                const audio = new Audio(audioLink);
                audio.addEventListener('ended', () => {
                    fetch('/api/reset_audio_status', { method: 'POST' });
                    audioPlaying = false;
                });
                audio.play().then(() => {
                    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    const analyser = audioCtx.createAnalyser();
                    const source = audioCtx.createMediaElementSource(audio);
                    source.connect(analyser);
                    analyser.connect(audioCtx.destination);
                    const dataArray = new Uint8Array(analyser.frequencyBinCount);
                    (function analyseVolume() {
                        analyser.getByteFrequencyData(dataArray);
                        modelController.setMouthOpenY(dataArray.reduce((a, b) => a + b, 0) / dataArray.length / 255);
                        if (!audio.paused) requestAnimationFrame(analyseVolume);
                    })();
                });
            })();
        });
    });

    vad.MicVAD.new({
        onSpeechStart: () => {
            if (!isProcessing && !audioPlaying) {
                mediaRecorder.start();
                statusDiv.textContent = "Listening...";
            }
        },
        onSpeechEnd: () => {
            if (!isProcessing && !audioPlaying) {
                mediaRecorder.stop();
                isProcessing = true;
                statusDiv.textContent = "Processing...";
            }
        }
    }).start();
})();