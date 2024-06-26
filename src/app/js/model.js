class ModelController {
    constructor(app, modelPath) {
        this.app = app;
        this.modelPath = modelPath;
        this.model = null;
    }

    async loadModel() {
        this.model = await this.loadNewModel();
        window.addEventListener('resize', () => this.loadNewModel());
        return this.model;
    }

    async loadNewModel() {
        if (this.model) {
            this.app.stage.removeChild(this.model);
            this.model.destroy();
        }

        this.model = await PIXI.live2d.Live2DModel.from(this.modelPath + "?v=" + new Date().getTime());
        this.app.stage.addChild(this.model);
        this.model.internalModel.coreModel.setParameterValueById('ParamMouthForm', 1);
        this.resizeModel();
        return this.model;
    }

    resizeModel() {
        if (!this.model) return;
        const scale = Math.min(window.innerWidth / this.model.width, window.innerHeight / this.model.height);
        this.model.scale.set(scale, scale);
        this.model.anchor.set(0.5, 0.5);
        this.model.position.set(window.innerWidth / 2, window.innerHeight / 2);
    }

    setMouthOpenY(v) {
        v *= 8;
        this.model.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', Math.max(0, Math.min(1, v)));
    }

    blink() {
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
                        this.updateEyeParameters(blinkValue);
                    }, 10);
                }, 100);
            }
            this.updateEyeParameters(blinkValue);
        }, 10);
    }

    startBlinking() {
        setInterval(() => this.blink(), Math.random() * 4000 + 2000);
    }

    updateEyeParameters(blinkValue) {
        this.model.internalModel.coreModel.setParameterValueById('ParamEyeLOpen', blinkValue);
        this.model.internalModel.coreModel.setParameterValueById('ParamEyeROpen', blinkValue);
    }
}

export default ModelController;
