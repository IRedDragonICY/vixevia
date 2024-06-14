import logging
import threading
import os
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from Chatbot import Chatbot
from pyngrok import ngrok

logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("so_vits_svc_fork").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)
logging.disable(logging.CRITICAL)
logging.disable(logging.ERROR)
app = FastAPI()

# Determine the absolute path to the model directory
current_dir = os.path.dirname(os.path.abspath(__file__))
model_dir = os.path.join(current_dir, "model/live2d")

# Mounting the directories to serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/js", StaticFiles(directory="static/js"), name="js")
app.mount("/temp", StaticFiles(directory="temp"), name="temp")
app.mount("/model/live2d", StaticFiles(directory=model_dir), name="live2d")

chatbot = Chatbot()

@app.get("/")
async def index():
    with open('static/index.html', 'r') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/api/audio_status")
async def get_audio_status():
    return {"audio_ready": chatbot.audio_ready}

@app.post("/api/reset_audio_status")
async def reset_audio_status():
    chatbot.audio_ready = False
    return {"audio_ready": chatbot.audio_ready}

@app.post("/api/upload_frame")
async def upload_frame(image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
        frame = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        chatbot.process_frame(frame)
    except Exception as e:
        print(f"Error processing frame: {e}")

@app.post("/api/upload_audio")
async def upload_audio(audio: UploadFile = File(...)):
    try:
        audio_bytes = await audio.read()
        chatbot.process_audio(audio_bytes)
    except Exception as e:
        print(f"Error processing audio: {e}")

def run_server():
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)

if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    public_url = ngrok.connect("8000")
    print(f"Public URL: {public_url}")
    ngrok_process = ngrok.get_ngrok_process()

    try:
        ngrok_process.proc.wait()
    except KeyboardInterrupt:
        print(" Shutting down server.")
        ngrok.kill()
