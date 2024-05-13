const app = new PIXI.Application({
    view: document.getElementById("canvas"),
    autoStart: true,
    resizeTo: window
});

let model;
loadModel().then((result) => model = result);

let video = setupVideo();

let audioPlaying = false;
const audio_link = "/temp/response.wav";
let volume = 1;
const statusDiv = document.getElementById('status');

async function loadModel() {
    const cubism2Model = "/model/live2d/vixevia.model3.json";
    const model = await PIXI.live2d.Live2DModel.from(cubism2Model);
    app.stage.addChild(model);
    model.scale.set(0.3);
    return model;
}

function setupVideo() {
    let video = document.createElement('video');
    video.autoplay = true;
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(function(stream) {
            video.srcObject = stream;
        })
        .catch(function(err) {
            console.log("Something went wrong!", err);
        });
    video.addEventListener('canplaythrough', function() {
        setInterval(captureFrame, 1000);
    }, false);
    return video;
}

function captureFrame() {
    if (video.readyState === 4) {
        let canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        new Promise((resolve, reject) => {
            canvas.toBlob(blob => {
                if (blob) {
                    resolve(blob);
                } else {
                    reject(new Error('Blob creation failed'));
                }
            }, 'image/jpeg');
        })
            .then(sendFrameToServer)
            .catch(error => console.error(error));
    }
}

function sendFrameToServer(blob) {
    let formData = new FormData();
    formData.append('image', blob, 'frame.jpg');
    fetch('/upload_frame', {method: 'POST', body: formData}).then(response => console.log(response));
}

async function initiateAudioPlay() {
    if (audioPlaying)
        return;
    await playAudioWhenReady();
}

async function checkAudioStatus() {
    return (await fetch('/audio_status').then(res => res.json())).audio_ready;
}

async function playAudioWhenReady() {
    while (true) {
        const audioReady = await checkAudioStatus();
        if (audioReady) {
            audioPlaying = true;
            let audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            let analyser = audioCtx.createAnalyser();
            analyser.fftSize = 32;
            let dataArray = new Uint8Array(analyser.frequencyBinCount);
            const audio = new Audio(audio_link);
            audio.volume = volume;
            await audio.play();
            let source = audioCtx.createMediaElementSource(audio);
            source.connect(analyser);
            analyser.connect(audioCtx.destination);
            function analyseVolume() {
                analyser.getByteFrequencyData(dataArray);
                let total = dataArray.reduce((prev, curr) => prev + curr, 0);
                let avg = total / dataArray.length;
                let volume = avg / 255;
                setMouthOpenY(volume);
                if (!audio.paused) {
                    requestAnimationFrame(analyseVolume);
                }
            }
            analyseVolume();
            audio.onended = async function() {
                await fetch('/reset_audio_status');
                audioPlaying = false;
                initiateAudioPlay();
                recognition.start();
            }
            break;
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
}

function setMouthOpenY(v){
    v = Math.max(0,Math.min(1,v));
    model.internalModel.coreModel.setParameterValueById('ParamMouthOpenY',v);
}

const recognition = new webkitSpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;
recognition.onstart = function() {
    statusDiv.innerHTML = "Listening...";
    mediaRecorder.start();
};
recognition.onend = function() {
    statusDiv.innerHTML = "Processing...";
    mediaRecorder.stop();
};
recognition.onerror = function(event) {
    console.error('Speech recognition error:', event.error);
    statusDiv.innerHTML = "";
};

const constraints = { audio: true };
let mediaRecorder;
let chunks = [];

navigator.mediaDevices.getUserMedia(constraints)
    .then(stream => {
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = event => {
            chunks.push(event.data);
        };
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(chunks, { type: 'audio/wav' });
            chunks = [];
            sendAudioToServer(audioBlob);
        };
        recognition.start();
    })
    .catch(err => {
        console.error('Error accessing microphone:', err);
    });

function sendAudioToServer(blob) {
    let formData = new FormData();
    formData.append('audio', blob, 'audio.wav');
    fetch('/upload_audio', { method: 'POST', body: formData })
        .then(response => {
            console.log(response);
            statusDiv.innerHTML = "";
        })
        .catch(error => console.error('Error uploading audio:', error));
}

initiateAudioPlay();