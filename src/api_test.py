import google.generativeai as genai
import concurrent.futures
import configparser


def print_green(text):
    print('\033[92m' + text + '\033[0m')


def print_red(text):
    print('\033[91m' + text + '\033[0m')


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


config = configparser.ConfigParser()
config.read('config.ini')
api_keys = config['API']['api_keys'].split(',')

results = list(concurrent.futures.ThreadPoolExecutor().map(check_key, api_keys))

valid_keys = sum(results)
invalid_keys = [key for key, valid in zip(api_keys, results) if not valid]

if valid_keys == len(api_keys):
    print_green(f"\n\nTotal valid API keys: {valid_keys}. All keys are valid!")
else:
    print(f"\n\nTotal valid API keys: {valid_keys}")
    if invalid_keys:
        print_red(f"Invalid API keys: {', '.join(invalid_keys)}")