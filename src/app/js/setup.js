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
    let isProcessing = false;
    let chunks = [];
    const audioLink = "/temp/response.wav";
    let audioPlaying = false;
    let audio;

    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });

    const video = document.createElement('video');
    video.srcObject = stream;
    video.autoplay = true;
    video.muted = true;
    video.addEventListener('canplay', () => {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        const captureFrame = () => {
            if (video.readyState === 4) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
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

    const mediaRecorder = new MediaRecorder(stream);
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

    const checkAudioReady = async () => {
        while (true) {
            const response = await fetch('/api/audio_status');
            const data = await response.json();
            if (data.audio_ready) {
                playBotAudio();
                break;
            }
            await new Promise(r => setTimeout(r, 500));
        }
    };

    const playBotAudio = () => {
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
                modelController.setMouthOpenY(dataArray.reduce((a, b) => a + b, 0) / dataArray.length / 255);
                if (!audio.paused) requestAnimationFrame(analyseVolume);
            };
            analyseVolume();
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
})();
