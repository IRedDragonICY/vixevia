import google.generativeai as genai
import pickle
import simpleaudio as sa
from google.generativeai.types import generation_types
import speech_recognition as sr
from gtts import gTTS
from pathlib import Path
from so_vits_svc_fork.inference.main import infer

class Chatbot:
    MODEL_NAME = "gemini-1.0-pro-001"
    HARM_CATEGORIES = ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]
    BLOCK_NONE = "BLOCK_NONE"
    MAX_OUTPUT_TOKENS = 999999999
    TOP_K = 1
    TOP_P = 1
    TEMPERATURE = 0.7

    def __init__(self):
        self.api_key = self.load_from_file('api_key.txt')
        self.system_prompt = self.load_from_file('system_prompt.txt')
        self.generation_config, self.safety_settings = self.model_config()
        self.model = self.get_model()
        self.convo = self.get_convo()
        self.convo.send_message({"role": "user", "parts": [{"text": self.system_prompt}]})

    def load_from_file(self, filename):
        with open(filename, 'r') as f:
            return f.read().splitlines()[0]

    def model_config(self):
        generation_config = generation_types.GenerationConfig(
            temperature=self.TEMPERATURE,
            top_p=self.TOP_P,
            top_k=self.TOP_K,
            max_output_tokens=self.MAX_OUTPUT_TOKENS,
        )
        safety_settings = [{"category": cat, "threshold": self.BLOCK_NONE} for cat in self.HARM_CATEGORIES]
        return generation_config, safety_settings

    def get_model(self):
        genai.configure(api_key=self.api_key)
        return genai.GenerativeModel(model_name=self.MODEL_NAME,
                                     generation_config=self.generation_config,
                                     safety_settings=self.safety_settings)

    def get_convo(self):
        history = []
        if Path('session.pkl').exists():
            with open('session.pkl', 'rb') as f:
                try:
                    history = pickle.load(f)
                except EOFError:
                    pass
        return self.model.start_chat(history=history)

    def user_input(self):
        return input("User: ")

    def save_convo(self):
        with open('session.pkl', 'wb') as f:
            pickle.dump(self.convo.history, f)

    def user_input_speech(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source)
            r.energy_threshold = 40000
            print("Listening...")
            audio = r.listen(source)
            try:
                print("Processing...")
                return r.recognize_google(audio, language='id-ID')
            except sr.UnknownValueError:
                return "..."

    def play_audio(self, file_path):
        wave_obj = sa.WaveObject.from_wave_file(file_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()

    def start_chat(self):
        while True:
            user_input = self.user_input_speech()
            print(f"User: {user_input}")
            response = "".join(chunk.text for chunk in self.convo.send_message(user_input))
            Path("response.mp3").unlink(missing_ok=True)
            gTTS(text=response, lang='id').save("temp/response.mp3")
            model_path = Path("model/audio/audio.pth")
            config_path = Path("model/audio/audio.json")
            output_path = Path("temp/response.wav")
            input_path = Path("temp/response.mp3")
            max_chunk_seconds = 95
            device = "cuda"
            infer(
                input_path=input_path,
                output_path=output_path,
                model_path=model_path,
                config_path=config_path,
                max_chunk_seconds=max_chunk_seconds,
                device=device,
                speaker="",
            )

            self.play_audio("temp/response.wav")
            self.save_convo()


if __name__ == "__main__":
    chatbot = Chatbot()
    chatbot.start_chat()