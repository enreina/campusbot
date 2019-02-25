from telegram.ext import Updater, CommandHandler
import logging
import settings as env
from dialoguemanager.response import generalCopywriting
from hc.taskExecutioner import TaskExecutioner

updater = Updater(token=env.TELEGRAM_BOT_TOKEN)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

## command handlers
def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=generalCopywriting.WELCOME_MESSAGE, parse_mode='Markdown')
                
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

taskExecutionerByChatId = {}

# def place_handler_wrapper(bot, update):
#     chatId = update.message.chat_id
#     if chatId not in taskExecutionerByChatId:
#         taskExecutionerByChatId[chatId] = TaskExecutioner('create-place', bot, update)
#     taskExecutioner = taskExecutionerByChatId[chatId]
#     taskExecutioner.startTask()

taskExecutioner = TaskExecutioner('create-place')
dispatcher.add_handler(taskExecutioner.conversationHandler)


updater.start_webhook(listen='0.0.0.0', port=env.PORT, url_path=env.TELEGRAM_BOT_TOKEN, webhook_url=env.NGROK_CAMPUSBOT_URL+'/'+env.TELEGRAM_BOT_TOKEN)
updater.bot.set_webhook(env.NGROK_CAMPUSBOT_URL+'/'+env.TELEGRAM_BOT_TOKEN)
updater.idle()