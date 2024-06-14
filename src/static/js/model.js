import { app } from './main.js';

let model;

export async function loadModel() {
    model = await PIXI.live2d.Live2DModel.from("../model/live2d/vixevia.model3.json?v=" + new Date().getTime());
    app.stage.addChild(model);
    model.scale.set(0.3);
    model.internalModel.coreModel.setParameterValueById('ParamMouthForm', 1);
    return model;
}

export function setMouthOpenY(v){
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
