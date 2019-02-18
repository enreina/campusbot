from telegram.ext import Updater, CommandHandler
import logging
from dotenv import load_dotenv, find_dotenv
import os
from dialoguemanager.response import generalCopywriting

load_dotenv(find_dotenv())

NGROK_CAMPUSBOT_URL = os.getenv('NGROK_CAMPUSBOT_URL')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PORT = int(os.getenv('PORT'))

updater = Updater(token=TELEGRAM_BOT_TOKEN)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

## command handlers
def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=generalCopywriting.WELCOME_MESSAGE, parse_mode='Markdown')
                
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TELEGRAM_BOT_TOKEN, webhook_url=NGROK_CAMPUSBOT_URL+'/'+TELEGRAM_BOT_TOKEN)
updater.bot.set_webhook(NGROK_CAMPUSBOT_URL+'/'+TELEGRAM_BOT_TOKEN)
updater.idle()