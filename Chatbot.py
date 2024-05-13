import pickle
import re
import time
from pathlib import Path

import cv2
import google.generativeai as genai
from google.generativeai.types import generation_types
from gtts import gTTS
from so_vits_svc_fork.inference.main import infer

from Config import Config


class Chatbot:
    def __init__(self):
        self.CONFIG = Config()
        self.api_keys = self._load_from_file(self.CONFIG.FILES["API_KEY"])
        self.api_key_index = 0
        self.system_prompt = self._load_from_file(self.CONFIG.FILES["SYSTEM_PROMPT"])
        self.generation_config, self.safety_settings = self._model_config()
        self.model = self._get_text_model()
        self.convo = self._get_convo()
        if not self.convo.history:
            self.convo.send_message({"role": "user", "parts": [{"text": self.system_prompt}]})
        self.frames = []
        self.audio_ready = False

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

    def _get_model(self, api_keys_range, model_name, config):
        selected_api_keys = self.api_keys[api_keys_range]
        self._configure_genai(selected_api_keys)
        return genai.GenerativeModel(
            model_name=model_name,
            generation_config=config,
            safety_settings=self.safety_settings,
            system_instruction=self.system_prompt
        )

    def _get_text_model(self):
        return self._get_model(slice(0, 3), self.CONFIG["MODEL_NAME"], self.generation_config)

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

    def _handle_response(self, user_input):
        for _ in range(10):
            try:
                response = "".join(chunk.text for chunk in self.convo.send_message(user_input))
                break
            except Exception as e:
                print(f"Exception occurred: {e}. Retrying...")
                self.api_key_index = (self.api_key_index + 1) % len(self.api_keys)
                self._configure_genai(self.api_keys)
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
