import logging
import webbrowser
import threading
import torch
from fastapi import FastAPI, File, UploadFile

from fastapi.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from Chatbot import Chatbot
import cv2
import numpy as np

logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("so_vits_svc_fork").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)
logging.disable(logging.CRITICAL)
logging.disable(logging.ERROR)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/js", StaticFiles(directory="static/js"), name="js")
app.mount("/model", StaticFiles(directory="model"), name="model")
app.mount("/temp", StaticFiles(directory="temp"), name="temp")
chatbot = Chatbot()


@app.get("/")
async def read_items():
    with open('static/index.html', 'r') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)



@app.get("/audio_status")
async def get_audio_status():
    return {"audio_ready": chatbot.audio_ready}


@app.get("/reset_audio_status")
async def reset_audio_status():
    chatbot.audio_ready = False
    return {"audio_ready": chatbot.audio_ready}


@app.post("/upload_frame")
async def upload_frame(image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
        image_array = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        chatbot.process_frame(frame)
    except Exception as e:
        print(f"Error processing frame: {e}")

@app.post("/upload_audio")
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
    webbrowser.open("http://localhost:8000/")
