const app = new PIXI.Application({ view: document.getElementById("canvas"), autoStart: true, resizeTo: window });
const audio_link = "/temp/response.wav";
const statusDiv = document.getElementById('status');

let model, video, audioPlaying = false, volume = 1;

loadModel().then(result => model = result);
setupVideo();

async function loadModel() {
    const model = await PIXI.live2d.Live2DModel.from("/model/live2d/vixevia.model3.json");
    app.stage.addChild(model);
    model.scale.set(0.3);
    return model;
}

function setupVideo() {
    video = document.createElement('video');
    video.autoplay = true;
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => video.srcObject = stream)
        .catch(err => console.log("Something went wrong!", err));
    video.addEventListener('canplaythrough', () => setInterval(captureFrame, 1000), false);
}

function captureFrame() {
    if (video.readyState !== 4) return;
    let canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(blob => blob ? sendFrameToServer(blob) : console.error('Blob creation failed'), 'image/jpeg');
}

function sendFrameToServer(blob) {
    let formData = new FormData();
    formData.append('image', blob, 'frame.jpg');
    fetch('/upload_frame', { method: 'POST', body: formData }).then(console.log);
}

async function initiateAudioPlay() {
    if (!audioPlaying) await playAudioWhenReady();
}

async function checkAudioStatus() {
    return (await fetch('/audio_status').then(res => res.json())).audio_ready;
}

async function playAudioWhenReady() {
    while (true) {
        if (await checkAudioStatus()) {
            audioPlaying = true;
            let audio = new Audio(audio_link);
            audio.volume = volume;
            await audio.play();
            setupAnalyser(audio);
            break;
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
}

function setupAnalyser(audio) {
    let audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    let analyser = audioCtx.createAnalyser();
    let dataArray = new Uint8Array(analyser.frequencyBinCount);
    let source = audioCtx.createMediaElementSource(audio);
    source.connect(analyser);
    analyser.connect(audioCtx.destination);
    analyseVolume(analyser, dataArray, audio);
    audio.onended = async function() {
        await fetch('/reset_audio_status');
        audioPlaying = false;
        initiateAudioPlay();
        recognition.start();
    }
}

function analyseVolume(analyser, dataArray, audio) {
    analyser.getByteFrequencyData(dataArray);
    let total = dataArray.reduce((prev, curr) => prev + curr, 0);
    let volume = total / dataArray.length / 255;
    setMouthOpenY(volume);
    if (!audio.paused) requestAnimationFrame(() => analyseVolume(analyser, dataArray, audio));
}

function setMouthOpenY(v){
    model.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', Math.max(0,Math.min(1,v)));
}

const recognition = new webkitSpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;
recognition.onstart = () => { statusDiv.innerHTML = "Listening..."; mediaRecorder.start(); };
recognition.onend = () => { statusDiv.innerHTML = "Processing..."; mediaRecorder.stop(); };
recognition.onerror = event => { console.error('Speech recognition error:', event.error); statusDiv.innerHTML = ""; };

let mediaRecorder, chunks = [];

navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = event => chunks.push(event.data);
        mediaRecorder.onstop = () => sendAudioToServer(new Blob(chunks, { type: 'audio/wav' }));
        chunks = [];
        recognition.start();
    })
    .catch(err => console.error('Error accessing microphone:', err));

function sendAudioToServer(blob) {
    let formData = new FormData();
    formData.append('audio', blob, 'audio.wav');
    fetch('/upload_audio', { method: 'POST', body: formData })
        .then(response => { console.log(response); statusDiv.innerHTML = ""; })
        .catch(error => console.error('Error uploading audio:', error));
}

initiateAudioPlay();
