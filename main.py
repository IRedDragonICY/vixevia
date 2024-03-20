from transformers import pipeline
from datetime import datetime
import re
import google.generativeai as genai
import pickle
import simpleaudio as sa
from google.generativeai.types import generation_types
from gtts import gTTS
from pathlib import Path
from so_vits_svc_fork.inference.main import infer
import speech_recognition as sr
import logging

logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("so_vits_svc_fork").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)
logging.disable(logging.CRITICAL)
logging.disable(logging.ERROR)

class Chatbot:
    CONFIG = {
        "MODEL_NAME": "gemini-1.0-pro-001",
        "HARM_CATEGORIES": ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            "HARM_CATEGORY_DANGEROUS_CONTENT"],
        "BLOCK_NONE": "BLOCK_NONE",
        "MAX_OUTPUT_TOKENS": 999999999,
        "TOP_K": 1,
        "TOP_P": 1,
        "TEMPERATURE": 0.7,
        "FILES": {
            "API_KEY": 'api_key.txt',
            "SYSTEM_PROMPT": 'system_prompt.txt',
            "SESSION": 'session.pkl',
            "RESPONSE_MP3": "temp/response.mp3",
            "RESPONSE_WAV": "temp/response.wav",
            "MODEL_PATH": "model/audio/audio.pth",
            "CONFIG_PATH": "model/audio/audio.json",
            "USER_INPUT": "temp/user_input.mp3"
        },
        "MAX_CHUNK_SECONDS": 95,
        "DEVICE": "cuda"
    }

    def __init__(self):
        self.api_keys = self._load_from_file(self.CONFIG["FILES"]["API_KEY"])
        self.api_key_index = 0
        self.system_prompt = self._load_from_file(self.CONFIG["FILES"]["SYSTEM_PROMPT"])
        self.generation_config, self.safety_settings = self._model_config()
        self.model = self._get_model()
        self.convo = self._get_convo()
        if not self.convo.history:
            self.convo.send_message({"role": "user", "parts": [{"text": self.system_prompt}]})
        self.transcriber = pipeline(
            "automatic-speech-recognition",
            model="model/speech-recognition",
            device="cuda",
        )
        self.transcriber.model.config.forced_decoder_ids = (
            self.transcriber.tokenizer.get_decoder_prompt_ids(
                language="id",
                task="transcribe",
            )
        )

    def _load_from_file(self, filename):
        with open(filename, 'r') as f:
            return f.read().splitlines() if filename == self.CONFIG["FILES"]["API_KEY"] else '\n'.join(f.read().splitlines())

    def _model_config(self):
        generation_config = generation_types.GenerationConfig(
            temperature=self.CONFIG["TEMPERATURE"],
            top_p=self.CONFIG["TOP_P"],
            top_k=self.CONFIG["TOP_K"],
            max_output_tokens=self.CONFIG["MAX_OUTPUT_TOKENS"],
        )
        safety_settings = [{"category": cat, "threshold": self.CONFIG["BLOCK_NONE"]} for cat in self.CONFIG["HARM_CATEGORIES"]]
        return generation_config, safety_settings

    def _get_model(self):
        genai.configure(api_key=self.api_keys[self.api_key_index])
        self.api_key_index = (self.api_key_index + 1) % len(self.api_keys)
        return genai.GenerativeModel(model_name=self.CONFIG["MODEL_NAME"],
                                     generation_config=self.generation_config,
                                     safety_settings=self.safety_settings)

    def _get_convo(self):
        history = []
        if Path(self.CONFIG["FILES"]["SESSION"]).exists():
            with open(self.CONFIG["FILES"]["SESSION"], 'rb') as f:
                try:
                    history = pickle.load(f)
                except EOFError:
                    pass
        return self.model.start_chat(history=history)

    def _save_convo(self):
        with open(self.CONFIG["FILES"]["SESSION"], 'wb') as f:
            pickle.dump(self.convo.history, f)

    def _user_input_speech(self):
        r = sr.Recognizer()
        r.energy_threshold = 32000
        with sr.Microphone() as source:
            print("Listening...")
            audio = r.listen(source)
            print("Processing...")
            with open(self.CONFIG["FILES"]["USER_INPUT"], "wb") as f:
                f.write(audio.get_wav_data())
            transcription = self.transcriber(self.CONFIG["FILES"]["USER_INPUT"])
            return transcription['text']

    def _play_audio(self, file_path):
        sa.WaveObject.from_wave_file(file_path).play().wait_done()

    def _handle_response(self, user_input):
        response = "".join(chunk.text for chunk in self.convo.send_message(user_input))
        response = re.sub(r'\(.*?\)', '', response)
        Path(self.CONFIG["FILES"]["RESPONSE_MP3"]).unlink(missing_ok=True)
        gTTS(text=response, lang='id').save(self.CONFIG["FILES"]["RESPONSE_MP3"])
        infer(
            input_path=Path(self.CONFIG["FILES"]["RESPONSE_MP3"]),
            output_path=Path(self.CONFIG["FILES"]["RESPONSE_WAV"]),
            model_path=Path(self.CONFIG["FILES"]["MODEL_PATH"]),
            config_path=Path(self.CONFIG["FILES"]["CONFIG_PATH"]),
            max_chunk_seconds=self.CONFIG["MAX_CHUNK_SECONDS"],
            device=self.CONFIG["DEVICE"],
            speaker="",
            transpose=7,
        )
        self._play_audio(self.CONFIG["FILES"]["RESPONSE_WAV"])
        self._save_convo()

    def start_chat(self):
        while True:
            user_input = self._user_input_speech()
            user_input += f"\nTime:({datetime.now().strftime('%H:%M:%S')})"
            print(f"User: {user_input}")
            self._handle_response(user_input)


if __name__ == "__main__":
    chatbot = Chatbot()
    chatbot.start_chat()