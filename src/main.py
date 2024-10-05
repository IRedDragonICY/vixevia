import ctypes
import logging
import sys
import threading
import urllib.request
import webbrowser
from urllib.error import URLError

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
from pyngrok import ngrok
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from Chatbot import Chatbot

logging.disable(logging.CRITICAL)


class ServerApp:
    def __init__(self):
        self.app = FastAPI()
        self.setup_middlewares()
        self.mount_directories()
        self.chatbot = Chatbot()
        self.ngrok_process = None
        self.public_url = None

        self.ensure_internet_connection()

    def setup_middlewares(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def mount_directories(self):
        directories = {
            "/app": "app",
            "/assets": "app/assets",
            "/js": "app/js",
            "/temp": "temp",
            "/model/live2d": "model/live2d",
            "/CSS": "app/CSS"
        }
        for mount_point, directory in directories.items():
            self.app.mount(
                mount_point,
                StaticFiles(directory=directory),
                name=mount_point.strip("/")
            )

    @staticmethod
    def check_internet_connection():
        try:
            urllib.request.urlopen('https://google.com', timeout=5)
            return True
        except URLError:
            return False

    def ensure_internet_connection(self):
        while not self.check_internet_connection():
            result = ctypes.windll.user32.MessageBoxW(
                0,
                "Tidak ada koneksi internet. Silakan periksa koneksi Anda dan coba lagi.",
                "Error",
                0x05 | 0x10 | 0x1000
            )
            if result == 4:
                continue
            else:
                sys.exit()

    @staticmethod
    def open_browser():
        webbrowser.open_new("http://localhost:8000")

    async def index(self, ngrok_api_key: str = Cookie(default=None)):
        with open('app/index.html', 'r') as f:
            html_content = f.read()
        headers = {"ngrok_api_key": ngrok_api_key} if ngrok_api_key else {}
        return HTMLResponse(content=html_content, headers=headers)

    async def get_audio_status(self):
        return {"audio_ready": self.chatbot.audio_ready}

    async def reset_audio_status(self):
        self.chatbot.audio_ready = False
        return {"audio_ready": self.chatbot.audio_ready}

    async def upload_frame(self, image: UploadFile = File(...)):
        try:
            image_bytes = await image.read()
            frame = cv2.imdecode(
                np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
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
            return JSONResponse(
                content={"message": "Tidak ada koneksi internet."},
                status_code=500
            )
        if self.ngrok_process:
            return JSONResponse(
                content={"message": "Ngrok sudah berjalan.", "public_url": self.public_url},
                status_code=200
            )
        ngrok.set_auth_token(api_key)
        self.public_url = ngrok.connect(8000).public_url
        self.ngrok_process = ngrok.get_ngrok_process()
        threading.Thread(target=self.ngrok_process.proc.wait).start()
        return JSONResponse(
            content={"message": "Ngrok berhasil dimulai.", "public_url": self.public_url},
            status_code=200
        )

    async def stop_ngrok(self):
        if self.ngrok_process:
            ngrok.kill()
            self.ngrok_process = None
            self.public_url = None
            return JSONResponse(
                content={"message": "Ngrok berhasil dihentikan."},
                status_code=200
            )
        return JSONResponse(
            content={"message": "Ngrok tidak berjalan."},
            status_code=400
        )

    def run(self):
        threading.Thread(target=self.open_browser).start()
        uvicorn.run(self.app, host="localhost", port=8000)


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
