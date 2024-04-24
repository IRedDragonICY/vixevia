import logging
import webbrowser
import threading

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from Chatbot import Chatbot

logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("so_vits_svc_fork").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)
logging.disable(logging.CRITICAL)
logging.disable(logging.ERROR)

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount model files
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

def run_server():
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)

if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    import time

    time.sleep(1)

    webbrowser.open("http://localhost:8000/")

    chatbot.start_chat()
