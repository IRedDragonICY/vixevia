import { app } from './setup.js';

let model;

export async function loadModel() {
    model = await PIXI.live2d.Live2DModel.from("../model/live2d/vixevia.model3.json?v=" + new Date().getTime());
    app.stage.addChild(model);
    model.internalModel.coreModel.setParameterValueById('ParamMouthForm', 1);

    resizeModel();
    window.addEventListener('resize', resizeModel);

    return model;
}

function resizeModel() {
    const scale = Math.min(window.innerWidth / model.width, window.innerHeight / model.height);
    model.scale.set(scale, scale);
    model.position.set(window.innerWidth / 2, window.innerHeight / 2);
    model.anchor.set(0.5, 0.5);
}

export function setMouthOpenY(v){
    v *= 8;
    model.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', Math.max(0,Math.min(1,v)));
}

export function blink() {
    let blinkValue = 1;
    let blinkSpeed = 0.1;
    const blinkInterval = setInterval(() => {
        blinkValue -= blinkSpeed;
        if (blinkValue <= 0) {
            blinkValue = 0;
            clearInterval(blinkInterval);
            setTimeout(() => {
                const closeEyeInterval = setInterval(() => {
                    blinkValue += blinkSpeed;
                    if (blinkValue >= 1) {
                        blinkValue = 1;
                        clearInterval(closeEyeInterval);
                    }
                    model.internalModel.coreModel.setParameterValueById('ParamEyeLOpen', blinkValue);
                    model.internalModel.coreModel.setParameterValueById('ParamEyeROpen', blinkValue);
                }, 10);
            }, 100);
        }
        model.internalModel.coreModel.setParameterValueById('ParamEyeLOpen', blinkValue);
        model.internalModel.coreModel.setParameterValueById('ParamEyeROpen', blinkValue);
    }, 10);
}

export function startBlinking() {
    setInterval(blink, Math.random() * 4000 + 2000);
}