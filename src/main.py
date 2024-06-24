import logging
import threading
import os
import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles

from Chatbot import Chatbot
from pyngrok import ngrok

logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("so_vits_svc_fork").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)
logging.disable(logging.CRITICAL)
logging.disable(logging.ERROR)
app = FastAPI()

current_dir = os.path.dirname(os.path.abspath(__file__))
model_dir = os.path.join(current_dir, "model/live2d")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/js", StaticFiles(directory="static/js"), name="js")
app.mount("/temp", StaticFiles(directory="temp"), name="temp")
app.mount("/model/live2d", StaticFiles(directory=model_dir), name="live2d")
app.mount("/CSS", StaticFiles(directory="static/CSS"), name="CSS")

chatbot = Chatbot()
ngrok_process = None
public_url = None

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

@app.post("/api/start_ngrok")
async def start_ngrok(api_key: str = Form(...)):
    global ngrok_process, public_url
    if ngrok_process:
        return JSONResponse(content={"message": "Ngrok is already running.", "public_url": public_url}, status_code=200)
    ngrok.set_auth_token(api_key)
    public_url = ngrok.connect(8000)
    ngrok_process = ngrok.get_ngrok_process()
    threading.Thread(target=ngrok_process.proc.wait).start()
    return JSONResponse(content={"message": "Ngrok started successfully.", "public_url": public_url}, status_code=200)

@app.post("/api/stop_ngrok")
async def stop_ngrok():
    global ngrok_process
    if ngrok_process:
        ngrok.kill()
        ngrok_process = None
        public_url = None
        return JSONResponse(content={"message": "Ngrok stopped successfully."}, status_code=200)
    return JSONResponse(content={"message": "Ngrok is not running."}, status_code=400)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
