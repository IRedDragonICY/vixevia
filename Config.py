class Config:
    MODEL_NAME = "gemini-1.5-pro-latest"
    HARM_CATEGORIES = ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                       "HARM_CATEGORY_DANGEROUS_CONTENT"]
    BLOCK_NONE = "BLOCK_NONE"
    MAX_OUTPUT_TOKENS = 999999999
    TOP_K = 1
    TOP_P = 1
    TEMPERATURE = 0.85

    class FILES:
        API_KEY = 'api_key.txt'
        SYSTEM_PROMPT = 'system_prompt.txt'
        SESSION = 'session.pkl'
        RESPONSE_MP3 = "temp/response.mp3"
        RESPONSE_WAV = "temp/response.wav"
        MODEL_PATH = "model/audio/audio.pth"
        CONFIG_PATH = "model/audio/audio.json"

    DEVICE = "cuda"
    MAX_CHUNK_SECONDS = 35

    def __getitem__(self, item):
        return getattr(self, item)
