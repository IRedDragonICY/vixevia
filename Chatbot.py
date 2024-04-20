import pickle
import re
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
import google.generativeai as genai
import simpleaudio as sa
import speech_recognition as sr
from concurrent.futures import ThreadPoolExecutor
from google.generativeai.types import generation_types
from gtts import gTTS
from so_vits_svc_fork.inference.main import infer
from transformers import pipeline

from Config import Config


class Chatbot:
    def __init__(self):
        self.CONFIG = Config()
        self.api_keys = self._load_from_file(self.CONFIG.FILES["API_KEY"])
        self.api_key_index = 0
        self.system_prompt = self._load_from_file(self.CONFIG.FILES["SYSTEM_PROMPT"])
        self.vision_prompt = self._load_from_file(self.CONFIG.FILES["VISION_PROMPT"])
        self.generation_config, self.safety_settings = self._model_config()
        self.model = self._get_model()
        self.convo = self._get_convo()
        if not self.convo.history:
            self.convo.send_message({"role": "user", "parts": [{"text": self.system_prompt}]})
        self.transcriber = self._get_transcriber()
        self.vision_model = self._get_vision_model()
        self.vision_chat = ""
        self.frame = None
        self.vision_chat_ready = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=2)

    def _load_from_file(self, filename):
        with open(filename, 'r') as f:
            return f.read().splitlines() if filename == self.CONFIG["FILES"]["API_KEY"] else '\n'.join(
                f.read().splitlines())

    def _model_config(self):
        generation_config = generation_types.GenerationConfig(
            temperature=self.CONFIG["TEMPERATURE"],
            top_p=self.CONFIG["TOP_P"],
            top_k=self.CONFIG["TOP_K"],
            max_output_tokens=self.CONFIG["MAX_OUTPUT_TOKENS"],
        )
        safety_settings = [{"category": cat, "threshold": self.CONFIG["BLOCK_NONE"]} for cat in
                           self.CONFIG["HARM_CATEGORIES"]]
        return generation_config, safety_settings

    def _configure_genai(self, selected_api_keys):
        genai.configure(api_key=selected_api_keys[self.api_key_index])
        self.api_key_index = (self.api_key_index + 1) % len(selected_api_keys)

    def _get_model(self):
        selected_api_keys = self.api_keys[:3]
        self._configure_genai(selected_api_keys)
        return genai.GenerativeModel(
            model_name=self.CONFIG["MODEL_NAME"],
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
            system_instruction=self.system_prompt
        )

    def _get_transcriber(self):
        transcriber = pipeline(
            "automatic-speech-recognition",
            model=self.CONFIG["FILES"]["MODEL_SPEECHRECOGNITION_PATH"],
            device=self.CONFIG["DEVICE"],
        )
        transcriber.model.config.forced_decoder_ids = (
            transcriber.tokenizer.get_decoder_prompt_ids(
                language="id",
                task="transcribe",
            )
        )
        return transcriber

    def _get_vision_model(self):
        selected_api_keys = self.api_keys[3:7]
        self._configure_genai(selected_api_keys)
        return genai.GenerativeModel(
            model_name=self.CONFIG["VISION_CONFIG"]["MODEL_NAME"],
            generation_config=generation_types.GenerationConfig(
                temperature=self.CONFIG["VISION_CONFIG"]["TEMPERATURE"],
                top_p=self.CONFIG["VISION_CONFIG"]["TOP_P"],
                top_k=self.CONFIG["VISION_CONFIG"]["TOP_K"],
                max_output_tokens=self.CONFIG["VISION_CONFIG"]["MAX_OUTPUT_TOKENS"],
            ),
            safety_settings=self.safety_settings
        )

    def _generate_vision_content(self):
        print(f"{datetime.now().strftime('%H:%M:%S')} Video is ready")
        while True:
            if self.frame is None:
                continue
            time.sleep(2)
            ret, buffer = cv2.imencode('.jpg', self.frame)
            prompt_parts = [{"mime_type": "image/jpeg", "data": buffer.tobytes()}, self.vision_prompt]
            try:
                response = self.vision_model.generate_content(prompt_parts, safety_settings=self.safety_settings)
                if response.parts:
                    self.vision_chat += f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Vixevia Melihat:({response.text}))"
                    self.vision_chat_ready.set()
            except ValueError:
                continue

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
            r.adjust_for_ambient_noise(source)
            print("Listening...")
            audio = r.listen(source)
            print("Processing...")
            with open(self.CONFIG["FILES"]["USER_INPUT"], "wb") as f:
                f.write(audio.get_wav_data())
            transcription = self.transcriber(self.CONFIG["FILES"]["USER_INPUT"])
            # FIX BUG Whisper
            if transcription['text'] == " Thank you.":
                return " "
            return transcription['text']

    def _play_audio(self, file_path):
        sa.WaveObject.from_wave_file(file_path).play().wait_done()

    def _handle_response(self, user_input):
        for _ in range(10):
            try:
                response = "".join(chunk.text for chunk in self.convo.send_message(user_input))
                break
            except Exception as e:
                print(f"Exception occurred: {e}. Retrying...")
        else:
            print("Failed to send message after 3 attempts. Exiting.")
            return
        response = re.sub(r'\(.*?\)', '', response)
        if response.strip():
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
        self.vision_chat = ""

    def _capture_video(self):
        print(f"{datetime.now().strftime('%H:%M:%S')} Initializing...")
        cap = cv2.VideoCapture(0)
        last_saved_time = time.time()
        try:
            while True:
                ret, self.frame = cap.read()
                if not ret:
                    break
                if time.time() - last_saved_time >= 1:
                    last_saved_time = time.time()
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()

    def start_chat(self):
        self.executor.submit(self._capture_video)
        self.executor.submit(self._generate_vision_content)
        self.vision_chat_ready.wait()
        print(f"{datetime.now().strftime('%H:%M:%S')} Vision is ready")
        while True:
            user_input = f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} User: {self._user_input_speech()}"
            print(f"{user_input}")
            user_input += self.vision_chat
            self._handle_response(user_input)