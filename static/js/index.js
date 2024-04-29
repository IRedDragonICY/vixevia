var audioPlaying = false;

const cubism2Model = "/model/live2d/vixevia.model3.json";
(async function main() {
    const app = new PIXI.Application({
        view: document.getElementById("canvas"),
        autoStart: true,
        resizeTo: window
    });

    const model = await PIXI.live2d.Live2DModel.from(cubism2Model);
    app.stage.addChild(model);
    model.scale.set(0.3);
    const audio_link = "/temp/response.wav";
    var volume = 1;

    const setMouthOpenY = v=>{
        v = Math.max(0,Math.min(1,v));
        model.internalModel.coreModel.setParameterValueById('ParamMouthOpenY',v);
    }

    document.addEventListener('click', async function() {
        if (audioPlaying)
            return;
        document.removeEventListener('click', arguments.callee);
        playAudioWhenReady();
    });

    async function checkAudioStatus() {
        const response = await fetch('/audio_status');
        const status = await response.json();
        return status.audio_ready;
    }

    async function playAudioWhenReady() {
        while (true) {
            const audioReady = await checkAudioStatus();
            if (audioReady) {
                audioPlaying = true;

                var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                var analyser = audioCtx.createAnalyser();
                analyser.fftSize = 32;
                var dataArray = new Uint8Array(analyser.frequencyBinCount);

                const audio = new Audio(audio_link);
                audio.volume = volume;
                audio.play();

                var source = audioCtx.createMediaElementSource(audio);
                source.connect(analyser);
                analyser.connect(audioCtx.destination);

                function analyseVolume() {
                    analyser.getByteFrequencyData(dataArray);
                    var total = dataArray.reduce((prev, curr) => prev + curr, 0);
                    var avg = total / dataArray.length;
                    var volume = avg / 255;
                    setMouthOpenY(volume);
                    if (!audio.paused) {
                        requestAnimationFrame(analyseVolume);
                    }
                }
                analyseVolume();

                audio.onended = async function() {
                    await fetch('/reset_audio_status');
                    audioPlaying = false;
                    playAudioWhenReady();
                }

                break;
            }
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
})();