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


class ServerApp:
    def __init__(self):
        self.app = FastAPI()
        self.setup_middlewares()
        self.mount_directories()
        self.chatbot = Chatbot()
        self.ngrok_process = None
        self.public_url = None

    def setup_middlewares(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def mount_directories(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(current_dir, "model/live2d")
        self.app.mount("/app", StaticFiles(directory="app"), name="app")
        self.app.mount("/assets", StaticFiles(directory="app"), name="assets")
        self.app.mount("/js", StaticFiles(directory="app/js"), name="js")
        self.app.mount("/temp", StaticFiles(directory="temp"), name="temp")
        self.app.mount("/model/live2d", StaticFiles(directory=model_dir), name="live2d")
        self.app.mount("/CSS", StaticFiles(directory="app/CSS"), name="CSS")

    def check_internet_connection(self):
        try:
            urllib.request.urlopen('https://google.com', timeout=5)
            return True
        except urllib.request.URLError:
            return False

    def show_error_message(self):
        MB_RETRYCANCEL = 0x05
        IDRETRY = 4
        IDCANCEL = 2
        result = ctypes.windll.user32.MessageBoxW(0,
                                                  "No internet connection. Please check your connection and try again.",
                                                  "Error", MB_RETRYCANCEL | 0x10 | 0x1000)
        if result == IDRETRY:
            if not self.check_internet_connection():
                self.show_error_message()
            else:
                self.start_webview()
        elif result == IDCANCEL:
            sys.exit()

    async def index(self, ngrok_api_key: str = Cookie(default=None)):
        if not self.check_internet_connection():
            self.show_error_message()
            return JSONResponse(content={"message": "No internet connection."}, status_code=500)
        with open('app/index.html', 'r') as f:
            html_content = f.read()
        headers = {"ngrok_api_key": ngrok_api_key} if ngrok_api_key else {}
        return HTMLResponse(content=html_content, status_code=200, headers=headers)

    async def get_audio_status(self):
        return {"audio_ready": self.chatbot.audio_ready}

    async def reset_audio_status(self):
        self.chatbot.audio_ready = False
        return {"audio_ready": self.chatbot.audio_ready}

    async def upload_frame(self, image: UploadFile = File(...)):
        try:
            image_bytes = await image.read()
            frame = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
            self.chatbot.process_frame(frame)
        except Exception as e:
            logging.error(f"Error processing frame: {e}")

    async def upload_audio(self, audio: UploadFile = File(...)):
        try:
            audio_bytes = await audio.read()
            self.chatbot.process_audio(audio_bytes)
        except Exception as e:
            logging.error(f"Error processing audio: {e}")

    async def start_ngrok(self, api_key: str = Form(...)):
        if not self.check_internet_connection():
            self.show_error_message()
            return JSONResponse(content={"message": "No internet connection."}, status_code=500)
        if self.ngrok_process:
            return JSONResponse(content={"message": "Ngrok is already running.", "public_url": self.public_url},
                                status_code=200)
        ngrok.set_auth_token(api_key)
        self.public_url = ngrok.connect(8000).public_url
        self.ngrok_process = ngrok.get_ngrok_process()
        threading.Thread(target=self.ngrok_process.proc.wait).start()
        return JSONResponse(content={"message": "Ngrok started successfully.", "public_url": self.public_url},
                            status_code=200)

    async def stop_ngrok(self):
        if self.ngrok_process:
            ngrok.kill()
            self.ngrok_process = None
            self.public_url = None
            return JSONResponse(content={"message": "Ngrok stopped successfully."}, status_code=200)
        return JSONResponse(content={"message": "Ngrok is not running."}, status_code=400)

    def start_webview(self):
        webview.create_window("Vixevia", "http://localhost:8000", width=800, height=600, resizable=True)
        webview.start()

    def run(self):
        threading.Thread(target=uvicorn.run, args=(self.app,), kwargs={"host": "localhost", "port": 8000},
                         daemon=True).start()
        if self.check_internet_connection():
            self.start_webview()
        else:
            self.show_error_message()


if __name__ == "__main__":
    server_app = ServerApp()
    server_app.app.get("/")(server_app.index)
    server_app.app.get("/api/audio_status")(server_app.get_audio_status)
    server_app.app.post("/api/reset_audio_status")(server_app.reset_audio_status)
    server_app.app.post("/api/upload_frame")(server_app.upload_frame)
    server_app.app.post("/api/upload_audio")(server_app.upload_audio)
    server_app.app.post("/api/start_ngrok")(server_app.start_ngrok)
    server_app.app.post("/api/stop_ngrok")(server_app.stop_ngrok)
    server_app.run()
