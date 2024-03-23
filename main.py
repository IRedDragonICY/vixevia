import logging

from Chatbot import Chatbot

# Set logging levels
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("so_vits_svc_fork").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)
logging.disable(logging.CRITICAL)
logging.disable(logging.ERROR)

if __name__ == "__main__":
    chatbot = Chatbot()
    chatbot.start_chat()
