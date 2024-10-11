import logging
import threading
import urllib.request
import webbrowser
from fastapi import FastAPI, File, UploadFile, Form, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from Chatbot import Chatbot
import cv2
import numpy as np
import uvicorn
from pyngrok import ngrok

logging.disable(logging.CRITICAL)

class ServerApp:
    def __init__(self):
        self.app = FastAPI()
        self.chatbot = Chatbot()
        self.ngrok_process = None
        self.public_url = None
        self.setup_routes_and_middlewares()

    def setup_routes_and_middlewares(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        directories = {
            "/app": "app",
            "/assets": "app/assets",
            "/js": "app/js",
            "/temp": "temp",
            "/model/live2d": "model/live2d",
            "/CSS": "app/CSS"
        }
        for mount_point, directory in directories.items():
            self.app.mount(mount_point, StaticFiles(directory=directory), name=mount_point.strip("/"))
        self.app.get("/")(self.index)
        self.app.get("/api/audio_status")(self.get_audio_status)
        self.app.post("/api/reset_audio_status")(self.reset_audio_status)
        self.app.post("/api/upload_frame")(self.upload_frame)
        self.app.post("/api/upload_audio")(self.upload_audio)
        self.app.post("/api/start_ngrok")(self.start_ngrok)
        self.app.post("/api/stop_ngrok")(self.stop_ngrok)

    @staticmethod
    async def index(ngrok_api_key: str = Cookie(default=None)):
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
            frame = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
            self.chatbot.process_frame(frame)
            return JSONResponse(content={"message": "Frame processed successfully"}, status_code=200)
        except Exception as e:
            logging.error(f"Error processing frame: {e}")
            return JSONResponse(content={"message": "Failed to process frame"}, status_code=500)

    async def upload_audio(self, audio: UploadFile = File(...)):
        try:
            audio_bytes = await audio.read()
            self.chatbot.process_audio(audio_bytes)
            return JSONResponse(content={"message": "Audio processed successfully"}, status_code=200)
        except Exception as e:
            logging.error(f"Error processing audio: {e}")
            return JSONResponse(content={"message": "Failed to process audio"}, status_code=500)

    async def start_ngrok(self, api_key: str = Form(...)):
        if not self.check_internet_connection():
            return JSONResponse(content={"message": "Tidak ada koneksi internet."}, status_code=500)
        if self.ngrok_process:
            return JSONResponse(content={"message": "Ngrok sudah berjalan.", "public_url": self.public_url}, status_code=200)
        try:
            ngrok.set_auth_token(api_key)
            tunnel = ngrok.connect(8000)
            self.public_url = tunnel.public_url
            self.ngrok_process = ngrok.get_ngrok_process()
            threading.Thread(target=self.ngrok_process.proc.wait).start()
            return JSONResponse(content={"message": "Ngrok berhasil dimulai.", "public_url": self.public_url}, status_code=200)
        except Exception as e:
            logging.error(f"Error starting ngrok: {e}")
            return JSONResponse(content={"message": f"Error starting ngrok: {str(e)}"}, status_code=500)

    async def stop_ngrok(self):
        if self.ngrok_process:
            try:
                ngrok.kill()
                self.ngrok_process = None
                self.public_url = None
                return JSONResponse(content={"message": "Ngrok berhasil dihentikan."}, status_code=200)
            except Exception as e:
                logging.error(f"Error stopping ngrok: {e}")
                return JSONResponse(content={"message": f"Error stopping ngrok: {str(e)}"}, status_code=500)
        return JSONResponse(content={"message": "Ngrok tidak berjalan."}, status_code=400)

    @staticmethod
    def check_internet_connection():
        try:
            urllib.request.urlopen('https://google.com', timeout=5)
            return True
        except Exception:
            return False

    def run(self):
        threading.Thread(target=self.open_browser).start()
        uvicorn.run(self.app, host="localhost", port=8000)

    @staticmethod
    def open_browser():
        webbrowser.open_new("http://localhost:8000")

if __name__ == "__main__":
    server_app = ServerApp()
    server_app.run()