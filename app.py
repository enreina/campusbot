from telegram.ext import Updater, CommandHandler
import logging
from dialoguemanager.response import generalCopywriting

TELEGRAM_BOT_API_TOKEN = '555780883:AAEcrvyhYbYn_uzRZAdtSc8i3F4dPmTDuog'

updater = Updater(token=TELEGRAM_BOT_API_TOKEN)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

## command handlers
def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=generalCopywriting.WELCOME_MESSAGE, parse_mode='Markdown')
                
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

updater.start_polling()
updater.idle()