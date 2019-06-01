from dotenv import load_dotenv, find_dotenv
import os
load_dotenv(find_dotenv())

NGROK_CAMPUSBOT_URL = os.getenv('NGROK_CAMPUSBOT_URL')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PORT = int(os.getenv('PORT'))
FIRESTORE_SERVICE_ACCOUNT_PATH = os.getenv('FIRESTORE_SERVICE_ACCOUNT_PATH')
IMAGE_DOWNLOAD_PATH = os.getenv('IMAGE_DOWNLOAD_PATH')
IMAGE_URL_PREFIX = os.getenv('IMAGE_URL_PREFIX')
API_BASE_URL = os.getenv('CAMPUSBOT_API_BASE_URL')
MAINTENANCE_MODE = os.getenv('MAINTENANCE_MODE')