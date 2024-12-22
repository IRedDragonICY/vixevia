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

class Chatbot:
    def __init__(self, config):
        self.config = config
        self.api_keys = self.config.API_KEYS
        if not self.api_keys:
            raise ValueError("API key list is empty. Please provide at least one API key.")
        self.api_key_index = 0
        self.system_prompt = Path(self.config.FILES.SYSTEM_PROMPT).read_text().strip()
        self.generation_config = generation_types.GenerationConfig(
            temperature=self.config.TEMPERATURE,
            top_p=self.config.TOP_P,
            top_k=self.config.TOP_K,
            max_output_tokens=self.config.MAX_OUTPUT_TOKENS,
        )
        self.safety_settings = [{"category": cat, "threshold": self.config.BLOCK_NONE} for cat in self.config.HARM_CATEGORIES]
        self.frames = []
        self.audio_ready = False
        self.history = self._load_history()
        self._initialize_conversation()

    def _configure_genai(self):
        genai.configure(api_key=self.api_keys[self.api_key_index])

    def _rotate_api_key_and_reinitialize(self):
        self.api_key_index = (self.api_key_index + 1) % len(self.api_keys)
        self._configure_genai()
        self._initialize_model_and_conversation()

    def _initialize_model_and_conversation(self):
        self.model = genai.GenerativeModel(
            model_name=self.config.MODEL_NAME,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
            system_instruction=self.system_prompt
        )
        self.convo = self.model.start_chat(history=self.history)

    def _load_history(self):
        session_path = Path(self.config.FILES.SESSION)
        if session_path.exists():
            try:
                with session_path.open('r', encoding='utf-8') as f:
                    history = json.load(f)
                    return history if isinstance(history, list) else []
            except json.JSONDecodeError:
                return []
        return []

    def _save_history(self):
        session_path = Path(self.config.FILES.SESSION)
        with session_path.open('w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=4)

    def _initialize_conversation(self):
        max_attempts = len(self.api_keys)
        for _ in range(max_attempts):
            try:
                self._configure_genai()
                self._initialize_model_and_conversation()
                self._ensure_system_prompt()
                return
            except Exception as e:
                if 'quota' in str(e).lower():
                    self._rotate_api_key_and_reinitialize()
                else:
                    raise
        raise Exception("All API keys have been exhausted.")

    def _ensure_system_prompt(self):
        if not self.history:
            system_message = {"role": "user", "parts": [{"text": self.system_prompt}]}
            self._send_with_retry(system_message)

    def _send_with_retry(self, user_input):
        max_attempts = len(self.api_keys)
        for _ in range(max_attempts):
            try:
                response_chunks = self.convo.send_message(user_input)
                return "".join(chunk.text for chunk in response_chunks)
            except Exception as e:
                if 'quota' in str(e).lower():
                    self._rotate_api_key_and_reinitialize()
                else:
                    raise
        raise Exception("All API keys have been exhausted during message handling.")

    def _process_response(self, response):
        if response:
            response = re.sub(r'\(.*?\)', '', response).strip()
            response_mp3_path = Path(self.config.FILES.RESPONSE_MP3)
            response_mp3_path.unlink(missing_ok=True)
            gTTS(text=response, lang='id').save(response_mp3_path)
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

    def _handle_response(self, user_input):
        response = self._send_with_retry(user_input)
        self._process_response(response)
        self.history.append(user_input)
        self.history.append({"role": "model", "parts": [{"text": response}]})
        self._save_history()

    def process_frame(self, frame):
        self.frames.append(frame)

    def process_audio(self, audio_bytes):
        if not self.frames:
            return
        encoded_frames = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(cv2.imencode('.jpg', frame)[1]).decode('utf-8')
            }
            for frame in self.frames
        ]
        encoded_audio = base64.b64encode(audio_bytes).decode('utf-8')
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
