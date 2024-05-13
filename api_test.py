import google.generativeai as genai
import concurrent.futures


def print_green(text):
    print('\033[92m' + text + '\033[0m')


def check_key(api_key):
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-latest",
            generation_config={"temperature": 1, "top_p": 0.95, "top_k": 0, "max_output_tokens": 8192},
            safety_settings=[{"category": c, "threshold": "BLOCK_NONE"} for c in
                             ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
                              "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
        )
        model.start_chat(history=[]).send_message("Halo")
        return True
    except Exception:
        return False


with open('api_key.txt', 'r') as f:
    api_keys = f.read().splitlines()

results = list(concurrent.futures.ThreadPoolExecutor().map(check_key, api_keys))

valid_keys = sum(results)
if valid_keys == len(api_keys):
    print_green(f"\n\nTotal valid API keys: {valid_keys}. All keys are valid!")
else:
    print(f"\n\nTotal valid API keys: {valid_keys}")
