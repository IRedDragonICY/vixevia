import json
import re
from datetime import datetime
from pathlib import Path
import base64

import cv2
import google.generativeai as genai
from google.generativeai.types import generation_types
from gtts import gTTS
from so_vits_svc_fork.inference.main import infer

from Config import Config


class Chatbot:
    def __init__(self):
        self.config = Config()
        self.api_keys = self._load_api_keys()
        if not self.api_keys:
            raise ValueError("API key list is empty. Please provide at least one API key.")
        self.api_key_index = 0
        self.system_prompt = self._load_system_prompt()
        self.generation_config, self.safety_settings = self._model_config()
        self.model = self._get_text_model()
        self.history = self._load_history()
        self.convo = self._start_conversation()
        self._ensure_system_prompt()
        self.frames = []
        self.audio_ready = False

    def _load_api_keys(self):
        with open(self.config.FILES.API_KEY, 'r') as f:
            keys = [line.strip() for line in f if line.strip()]
            print(f"Loaded {len(keys)} API keys.")
            return keys

    def _load_system_prompt(self):
        with open(self.config.FILES.SYSTEM_PROMPT, 'r') as f:
            return f.read().strip()

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

    def _mask_api_key(self, key):
        if len(key) > 6:
            return key[:-6] + '*' * 6
        return '*' * len(key)

    def _configure_genai(self):
        current_api_key = self.api_keys[self.api_key_index]
        genai.configure(api_key=current_api_key)
        masked_key = self._mask_api_key(current_api_key)
        print(f"Using API key index: {self.api_key_index} (Key: {masked_key})")

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

    def _load_history(self):
        session_path = Path(self.config.FILES.SESSION)
        if session_path.exists():
            try:
                with session_path.open('r', encoding='utf-8') as f:
                    history = json.load(f)
                    if isinstance(history, list):
                        print(f"Loaded history with {len(history)} messages.")
                        return history
            except json.JSONDecodeError:
                print("Session file corrupted or empty. Starting a new conversation.")
        return []

    def _save_history(self):
        session_path = Path(self.config.FILES.SESSION)
        try:
            with session_path.open('w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
            print(f"History saved with {len(self.history)} messages.")
        except Exception as e:
            print(f"Failed to save history: {e}")

    def _start_conversation(self):
        return self.model.start_chat(history=self.history)

    def _ensure_system_prompt(self):
        if not self.history:
            try:
                system_message = {"role": "user", "parts": [{"text": self.system_prompt}]}
                self.convo.send_message(system_message)
                self.history.append(system_message)
                self._save_history()
                print("System prompt initialized.")
            except Exception as e:
                print(f"Exception during system prompt initialization: {e}. Retrying...")
                self._rotate_api_key()
                self._ensure_system_prompt()

    def _rotate_api_key(self):
        previous_index = self.api_key_index
        self.api_key_index = (self.api_key_index + 1) % len(self.api_keys)
        if self.api_key_index == previous_index:
            print("All API keys have been exhausted.")
        else:
            print(f"Rotated API key to index {self.api_key_index}.")

    def _handle_response(self, user_input):
        max_attempts = len(self.api_keys)
        for attempt in range(max_attempts):
            try:
                response_chunks = self.convo.send_message(user_input)
                response = "".join(chunk.text for chunk in response_chunks)
                break
            except Exception as e:
                error_message = str(e).lower()
                print(f"Exception occurred: {e}.")
                if '429' in error_message or 'quota' in error_message or 'exhausted' in error_message:
                    print(f"Error 429 detected. Rotating API key. Attempt {attempt + 1}/{max_attempts}")
                    self._rotate_api_key()
                    self.model = self._get_text_model()
                else:
                    print("Non-rate limit error encountered. Retrying with the same API key.")
        else:
            print("All API keys have been exhausted. Failed to send message.")
            return

        response = re.sub(r'\(.*?\)', '', response).strip()
        if response:
            try:
                response_mp3_path = Path(self.config.FILES.RESPONSE_MP3)
                response_mp3_path.unlink(missing_ok=True)
                gTTS(text=response, lang='id').save(response_mp3_path)
                print(f"Saved response audio to {response_mp3_path}")

                infer(
                    input_path=response_mp3_path,
                    output_path=Path(self.config.FILES.RESPONSE_WAV),
                    model_path=Path(self.config.FILES.MODEL_PATH),
                    config_path=Path(self.config.FILES.CONFIG_PATH),
                    max_chunk_seconds=self.config.MAX_CHUNK_SECONDS,
                    device=self.config.DEVICE,
                    speaker="",
                    transpose=7,
                )
                self.audio_ready = True
                print("Audio inference completed.")
            except Exception as e:
                print(f"Failed to process audio: {e}")

        self.history.append(user_input)
        assistant_message = {"role": "assistant", "parts": [{"text": response}]}
        self.history.append(assistant_message)

        self._save_history()

    def process_frame(self, frame):
        self.frames.append(frame)
        print(f"Frame added. Total frames: {len(self.frames)}")

    def process_audio(self, audio_bytes):
        if not self.frames:
            print("No frames to process.")
            return

        try:
            encoded_frames = [
                {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(cv2.imencode('.jpg', frame)[1]).decode('utf-8')
                }
                for frame in self.frames
            ]
            print(f"Encoded {len(encoded_frames)} frames.")
        except Exception as e:
            print(f"Failed to encode frames: {e}")
            encoded_frames = []

        try:
            encoded_audio = base64.b64encode(audio_bytes).decode('utf-8')
            print("Audio encoded successfully.")
        except Exception as e:
            print(f"Failed to encode audio: {e}")
            encoded_audio = ""

        user_input = {
            "role": "user",
            "parts": [
                {"text": "Waktu: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                {"text": "Penglihatan Vixevia:"},
                *encoded_frames,
                {"text": "Pendengaran Vixevia:"},
                {"mime_type": "audio/wav", "data": encoded_audio},
            ],
        }
        self._handle_response(user_input)
        self.frames.clear()
        print("Frames cleared after processing audio.")
