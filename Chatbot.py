import pickle
import re
from pathlib import Path

import cv2
import google.generativeai as genai
from google.generativeai.types import generation_types
from gtts import gTTS
from so_vits_svc_fork.inference.main import infer

from Config import Config


class Chatbot:
    def __init__(self):
        self.config = Config()
        self.api_keys = self._load_from_file(self.config.FILES.API_KEY)
        self.api_key_index = 0
        self.system_prompt = self._load_from_file(self.config.FILES.SYSTEM_PROMPT)
        self.generation_config, self.safety_settings = self._model_config()
        self.model = self._get_text_model()
        self.convo = self._get_convo()
        if not self.convo.history:
            self.convo.send_message({"role": "user", "parts": [{"text": self.system_prompt}]})
        self.frames = []
        self.audio_ready = False

    def _load_from_file(self, filename):
        with open(filename, 'r') as f:
            return f.read().splitlines() if filename == self.config.FILES.API_KEY else '\n'.join(
                f.read().splitlines())

    def _model_config(self):
        generation_config = generation_types.GenerationConfig(
            temperature=self.config.TEMPERATURE,
            top_p=self.config.TOP_P,
            top_k=self.config.TOP_K,
            max_output_tokens=self.config.MAX_OUTPUT_TOKENS,
        )
        safety_settings = [{"category": cat, "threshold": self.config.BLOCK_NONE} for cat in
                           self.config.HARM_CATEGORIES]
        return generation_config, safety_settings

    def _configure_genai(self):
        genai.configure(api_key=self.api_keys[self.api_key_index])
        self.api_key_index = (self.api_key_index + 1) % len(self.api_keys)

    def _get_model(self, model_name, config):
        self._configure_genai()
        return genai.GenerativeModel(
            model_name=model_name,
            generation_config=config,
            safety_settings=self.safety_settings,
            system_instruction=self.system_prompt
        )

    def _get_text_model(self):
        return self._get_model(self.config.MODEL_NAME, self.generation_config)

    def _get_convo(self):
        history = []
        if Path(self.config.FILES.SESSION).exists():
            with open(self.config.FILES.SESSION, 'rb') as f:
                try:
                    history = pickle.load(f)
                except EOFError:
                    pass
        return self.model.start_chat(history=history)

    def _save_convo(self):
        with open(self.config.FILES.SESSION, 'wb') as f:
            pickle.dump(self.convo.history, f)

    def _handle_response(self, user_input):
        for _ in range(10):
            try:
                response = "".join(chunk.text for chunk in self.convo.send_message(user_input))
                break
            except Exception as e:
                print(f"Exception occurred: {e}. Retrying...")
                self._configure_genai()
        else:
            print("Failed to send message after 10 attempts. Exiting.")
            return
        response = re.sub(r'\(.*?\)', '', response)
        if response.strip():
            Path(self.config.FILES.RESPONSE_MP3).unlink(missing_ok=True)
            gTTS(text=response, lang='id').save(self.config.FILES.RESPONSE_MP3)
            infer(
                input_path=Path(self.config.FILES.RESPONSE_MP3),
                output_path=Path(self.config.FILES.RESPONSE_WAV),
                model_path=Path(self.config.FILES.MODEL_PATH),
                config_path=Path(self.config.FILES.CONFIG_PATH),
                max_chunk_seconds=self.config.MAX_CHUNK_SECONDS,
                device=self.config.DEVICE,
                speaker="",
                transpose=7,
            )
            self.audio_ready = True
        self._save_convo()

    def process_frame(self, frame):
        self.frames.append(frame)

    def process_audio(self, audio_bytes):
        user_input = {
            "role": "user",
            "parts": [
                {"text": "Penglihatan:"},
                *[
                    {"mime_type": "image/jpeg", "data": cv2.imencode('.jpg', frame)[1].tobytes()}
                    for frame in self.frames
                ],
                {"text": "Pendengaran:"},
                {"mime_type": "audio/wav", "data": audio_bytes},
            ],
        }
        self._handle_response(user_input)
        self.frames = []