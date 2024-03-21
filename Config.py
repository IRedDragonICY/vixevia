class Config:
    MODEL_NAME = "gemini-1.0-pro-001"
    HARM_CATEGORIES = ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                       "HARM_CATEGORY_DANGEROUS_CONTENT"]
    BLOCK_NONE = "BLOCK_NONE"
    MAX_OUTPUT_TOKENS = 999999999
    TOP_K = 1
    TOP_P = 1
    TEMPERATURE = 0.85
    VISION_CONFIG = {
        "MODEL_NAME": "gemini-1.0-pro-vision-latest",
        "TEMPERATURE": 0.3,
        "TOP_P": 1,
        "TOP_K": 32,
        "MAX_OUTPUT_TOKENS": 4096,
    }
    FILES = {
        "API_KEY": 'api_key.txt',
        "SYSTEM_PROMPT": 'system_prompt.txt',
        "VISION_PROMPT": 'vision_prompt.txt',
        "SESSION": 'session.pkl',
        "RESPONSE_MP3": "temp/response.mp3",
        "RESPONSE_WAV": "temp/response.wav",
        "MODEL_PATH": "model/audio/audio.pth",
        "MODEL_SPEECHRECOGNITION_PATH": "model/speech-recognition",
        "CONFIG_PATH": "model/audio/audio.json",
        "USER_INPUT": "temp/user_input.mp3"
    }
    MAX_CHUNK_SECONDS = 95
    DEVICE = "cuda"

    def __getitem__(self, item):
        return getattr(self, item)
