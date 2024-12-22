import configparser
import random
import os

class Config:
    def __init__(self, config_file='config.ini'):
        if not os.path.exists(config_file):
            self._create_default_config(config_file)
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        default = self.config['DEFAULT']
        self.MODEL_NAME = default.get('MODEL_NAME')
        self.BLOCK_NONE = default.get('BLOCK_NONE')
        self.MAX_OUTPUT_TOKENS = default.getint('MAX_OUTPUT_TOKENS')
        self.TOP_K = default.getint('TOP_K')
        self.TOP_P = default.getfloat('TOP_P')
        self.TEMPERATURE = default.getfloat('TEMPERATURE')
        self.DEVICE = default.get('DEVICE')
        self.MAX_CHUNK_SECONDS = default.getint('MAX_CHUNK_SECONDS')
        self.HARM_CATEGORIES = self.config['HARM_CATEGORIES'].get('categories').split(',')
        self.FILES = self.FilesConfig(self.config['FILES'])
        self.API_KEYS = [key.strip() for key in self.config['API']['API_KEYS'].split(',') if key.strip()]
        self.NGROK_API_KEY = self.config['NGROK'].get('api_key')

    @staticmethod
    def _create_default_config(config_file):
        default_config = '''[DEFAULT]
MODEL_NAME = gemini-2.0-flash-exp
BLOCK_NONE = BLOCK_NONE
MAX_OUTPUT_TOKENS = 8192
TOP_K = 1
TOP_P = 1.0
TEMPERATURE = 0.85
DEVICE = cuda
MAX_CHUNK_SECONDS = 35

[HARM_CATEGORIES]
categories = HARM_CATEGORY_HARASSMENT,HARM_CATEGORY_HATE_SPEECH,HARM_CATEGORY_SEXUALLY_EXPLICIT,HARM_CATEGORY_DANGEROUS_CONTENT

[FILES]
SYSTEM_PROMPT = system_prompt.txt
SESSION = session.json
RESPONSE_MP3 = temp/response.mp3
RESPONSE_WAV = temp/response.wav
MODEL_PATH = model/audio/audio.pth
CONFIG_PATH = model/audio/audio.json

[API]
API_KEYS = YOUR_API_KEYS_HERE
'''
        with open(config_file, 'w') as f:
            f.write(default_config)

    class FilesConfig:
        def __init__(self, files_section):
            self.SYSTEM_PROMPT = files_section.get('SYSTEM_PROMPT')
            self.SESSION = files_section.get('SESSION')
            self.RESPONSE_MP3 = files_section.get('RESPONSE_MP3')
            self.RESPONSE_WAV = files_section.get('RESPONSE_WAV')
            self.MODEL_PATH = files_section.get('MODEL_PATH')
            self.CONFIG_PATH = files_section.get('CONFIG_PATH')

    def get_api_key(self):
        return random.choice(self.API_KEYS)

    def __getitem__(self, item):
        return getattr(self, item)
