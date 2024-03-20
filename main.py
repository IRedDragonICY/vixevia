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


class Chatbot:
    MODEL_NAME = "gemini-1.0-pro-001"
    HARM_CATEGORIES = ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                       "HARM_CATEGORY_DANGEROUS_CONTENT"]
    BLOCK_NONE = "BLOCK_NONE"
    MAX_OUTPUT_TOKENS = 999999999
    TOP_K = 1
    TOP_P = 1
    TEMPERATURE = 0.7
    API_KEY_FILE = 'api_key.txt'
    SYSTEM_PROMPT_FILE = 'system_prompt.txt'
    SESSION_FILE = 'session.pkl'
    RESPONSE_MP3 = "temp/response.mp3"
    RESPONSE_WAV = "temp/response.wav"
    MODEL_PATH = "model/audio/audio.pth"
    CONFIG_PATH = "model/audio/audio.json"
    MAX_CHUNK_SECONDS = 95
    DEVICE = "cuda"

    def __init__(self):
        """Initialize the chatbot."""
        self.api_keys = self._load_from_file(self.API_KEY_FILE)
        self.api_key_index = 0
        self.system_prompt = self._load_from_file(self.SYSTEM_PROMPT_FILE)
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
            if filename == self.API_KEY_FILE:
                return f.read().splitlines()
            else:
                return '\n'.join(f.read().splitlines())

    def _model_config(self):
        generation_config = generation_types.GenerationConfig(
            temperature=self.TEMPERATURE,
            top_p=self.TOP_P,
            top_k=self.TOP_K,
            max_output_tokens=self.MAX_OUTPUT_TOKENS,
        )
        safety_settings = [{"category": cat, "threshold": self.BLOCK_NONE} for cat in self.HARM_CATEGORIES]
        return generation_config, safety_settings

    def _get_model(self):
        genai.configure(api_key=self.api_keys[self.api_key_index])
        self.api_key_index = (self.api_key_index + 1) % len(self.api_keys)
        return genai.GenerativeModel(model_name=self.MODEL_NAME,
                                     generation_config=self.generation_config,
                                     safety_settings=self.safety_settings)

    def _get_convo(self):
        history = []
        if Path(self.SESSION_FILE).exists():
            with open(self.SESSION_FILE, 'rb') as f:
                try:
                    history = pickle.load(f)
                except EOFError:
                    pass
        return self.model.start_chat(history=history)

    def _user_input(self):
        return input("User: ")

    def _save_convo(self):
        with open(self.SESSION_FILE, 'wb') as f:
            pickle.dump(self.convo.history, f)

    def _user_input_speech(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            audio = r.listen(source)
            print("Processing...")
            with open("temp/user_input.mp3", "wb") as f:
                f.write(audio.get_wav_data())
            transcription = self.transcriber("temp/user_input.mp3")
            print("Processing...")
            return transcription['text']

    def _play_audio(self, file_path):
        sa.WaveObject.from_wave_file(file_path).play().wait_done()

    def start_chat(self):
        while True:
            user_input = self._user_input_speech()
            user_input += f"\nTime:({datetime.now().strftime('%H:%M:%S')})"
            print(f"User: {user_input}")
            response = "".join(chunk.text for chunk in self.convo.send_message(user_input))
            response = re.sub(r'\(.*?\)', '', response)
            Path(self.RESPONSE_MP3).unlink(missing_ok=True)
            gTTS(text=response, lang='id').save(self.RESPONSE_MP3)
            infer(
                input_path=Path(self.RESPONSE_MP3),
                output_path=Path(self.RESPONSE_WAV),
                model_path=Path(self.MODEL_PATH),
                config_path=Path(self.CONFIG_PATH),
                max_chunk_seconds=self.MAX_CHUNK_SECONDS,
                device=self.DEVICE,
                speaker="",
            )

            self._play_audio(self.RESPONSE_WAV)
            self._save_convo()


if __name__ == "__main__":
    chatbot = Chatbot()
    chatbot.start_chat()
