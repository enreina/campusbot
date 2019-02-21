from dotenv import load_dotenv, find_dotenv
import os
load_dotenv(find_dotenv())

NGROK_CAMPUSBOT_URL = os.getenv('NGROK_CAMPUSBOT_URL')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PORT = int(os.getenv('PORT'))
FIRESTORE_SERVICE_ACCOUNT_PATH = os.getenv('FIRESTORE_SERVICE_ACCOUNT_PATH')