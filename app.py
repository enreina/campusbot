from telegram.ext import Updater, CommandHandler
import logging
import settings as env
from dialoguemanager.response import generalCopywriting
from hc.taskExecutioner import TaskExecutioner
from tasklist.taskListHandler import TaskListHandler
from startflow.startHandler import StartHandler

updater = Updater(token=env.TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

## command handlers
def start(update, context):
    # to-do: register user if this is their first time
    context.bot.send_message(chat_id=update.message.chat_id, text=generalCopywriting.WELCOME_MESSAGE, parse_mode='Markdown')
    context.bot.send_message(chat_id=update.message.chat_id, text=generalCopywriting.START_MESSAGE, parse_mode='Markdown')
                

startHandler = StartHandler(dispatcher)
taskListHandler = TaskListHandler('place', 'placeTaskInstances', 'Place', dispatcher)

updater.start_webhook(listen='0.0.0.0', port=env.PORT, url_path=env.TELEGRAM_BOT_TOKEN, webhook_url=env.NGROK_CAMPUSBOT_URL+'/'+env.TELEGRAM_BOT_TOKEN)
updater.bot.set_webhook(env.NGROK_CAMPUSBOT_URL+'/'+env.TELEGRAM_BOT_TOKEN)
updater.idle()