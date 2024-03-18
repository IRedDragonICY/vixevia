import google.generativeai as genai
import pickle
import os
import pygame
from google.generativeai.types import generation_types
import speech_recognition as sr
from gtts import gTTS


class Chatbot:
    def __init__(self):
        self.api_key = self._get_api_key()
        self.generation_config = self._get_generation_config()
        self.safety_settings = self._get_safety_settings()
        self.model = self._get_model()
        self.convo = self._get_convo()
        self.system_prompt = self._get_system_prompt()
        self.convo.send_message({"role": "user", "parts": [{"text": self.system_prompt}]})

    def _get_api_key(self):
        with open('api_key.txt', 'r') as f:
            return f.read().splitlines()[0]

    def _get_generation_config(self):
        return generation_types.GenerationConfig(
            temperature=0.7,
            top_p=1,
            top_k=1,
            max_output_tokens=999999999,
        )

    def _get_safety_settings(self):
        return [{"category": cat, "threshold": "BLOCK_NONE"} for cat in
                ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                 "HARM_CATEGORY_DANGEROUS_CONTENT"]]

    def _get_model(self):
        genai.configure(api_key=self.api_key)
        return genai.GenerativeModel(model_name="gemini-1.0-pro-001",
                                     generation_config=self.generation_config,
                                     safety_settings=self.safety_settings)

    def _get_convo(self):
        try:
            history = pickle.load(open('session.pkl', 'rb')) if os.path.exists('session.pkl') else []
        except EOFError:
            history = []
        return self.model.start_chat(history=history)

    def _get_system_prompt(self):
        with open('system_prompt.txt', 'r') as f:
            return f.read()

    def user_input(self):
        return input("User: ")

    def save_convo(self):
        with open('session.pkl', 'wb') as f:
            return pickle.dump(self.convo.history, f)

    def user_input_speech(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            r.adjust_for_ambient_noise(source)
            r.dynamic_energy_threshold = True
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio, language='id-ID')
                return text
            except sr.UnknownValueError:
                return "..."

    def play_audio(self, file_path):
        pygame.mixer.init()

        pygame.mixer.music.load(file_path)

        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    def start_chat(self):
        while True:
            user_input = self.user_input_speech()
            print("User: " + user_input)
            print("Vixevia: ", end="")
            response = ""
            for chunk in self.convo.send_message(user_input, stream=True):
                response += chunk.text
            print(response)
            gTTS(text=response, lang='id').save("response.mp3")
            self.play_audio("response.mp3")
            print()

            self.save_convo()


if __name__ == "__main__":
    chatbot = Chatbot()
    chatbot.start_chat()
