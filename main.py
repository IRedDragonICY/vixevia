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


@app.get("/")
async def read_items():
    with open('static/index.html', 'r') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)


def run_server():
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)


if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    import time

    time.sleep(1)

    chatbot = Chatbot()
    webbrowser.open("http://localhost:8000/")

    chatbot.start_chat()
