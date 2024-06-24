import logging
import threading
import os
import cv2
import numpy as np
import uvicorn
import webview
from fastapi import FastAPI, File, UploadFile, Form, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from Chatbot import Chatbot
from pyngrok import ngrok
import ctypes
import urllib.request
import sys

logging.disable(logging.CRITICAL)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

def check_internet_connection():
    try:
        urllib.request.urlopen('http://google.com', timeout=5)
        return True
    except urllib.request.URLError:
        return False

def show_error_message():
    MB_RETRYCANCEL = 0x05
    IDRETRY = 4
    IDCANCEL = 2
    result = ctypes.windll.user32.MessageBoxW(0, "No internet connection. Please check your connection and try again.", "Error", MB_RETRYCANCEL | 0x10 | 0x1000)
    if result == IDRETRY:
        if not check_internet_connection():
            show_error_message()
        else:
            start_webview()
    elif result == IDCANCEL:
        sys.exit()

@app.get("/")
async def index(ngrok_api_key: str = Cookie(default=None)):
    if not check_internet_connection():
        show_error_message()
        return JSONResponse(content={"message": "No internet connection."}, status_code=500)
    with open('static/index.html', 'r') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200, headers={"ngrok_api_key": ngrok_api_key} if ngrok_api_key else {})

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
        logging.error(f"Error processing frame: {e}")

@app.post("/api/upload_audio")
async def upload_audio(audio: UploadFile = File(...)):
    try:
        audio_bytes = await audio.read()
        chatbot.process_audio(audio_bytes)
    except Exception as e:
        logging.error(f"Error processing audio: {e}")

@app.post("/api/start_ngrok")
async def start_ngrok(api_key: str = Form(...)):
    global ngrok_process, public_url
    if not check_internet_connection():
        show_error_message()
        return JSONResponse(content={"message": "No internet connection."}, status_code=500)
    if ngrok_process:
        return JSONResponse(content={"message": "Ngrok is already running.", "public_url": public_url}, status_code=200)
    ngrok.set_auth_token(api_key)
    public_url = ngrok.connect(8000).public_url
    ngrok_process = ngrok.get_ngrok_process()
    threading.Thread(target=ngrok_process.proc.wait).start()
    return JSONResponse(content={"message": "Ngrok started successfully.", "public_url": public_url}, status_code=200)

@app.post("/api/stop_ngrok")
async def stop_ngrok():
    global ngrok_process, public_url
    if ngrok_process:
        ngrok.kill()
        ngrok_process = None
        public_url = None
        return JSONResponse(content={"message": "Ngrok stopped successfully."}, status_code=200)
    return JSONResponse(content={"message": "Ngrok is not running."}, status_code=400)

def start_webview():
    webview.create_window("Vixevia", "http://localhost:8000", width=800, height=600, resizable=True)
    webview.start()

if __name__ == "__main__":
    threading.Thread(target=uvicorn.run, args=(app,), kwargs={"host": "localhost", "port": 8000}, daemon=True).start()
    if check_internet_connection():
        start_webview()
    else:
        show_error_message()
