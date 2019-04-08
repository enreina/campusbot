from telegram.ext import Updater, CommandHandler
import logging
import settings as env
from dialoguemanager.response import generalCopywriting
from tasklist.taskListHandler import TaskListHandler
from startflow.startHandler import StartHandler

updater = Updater(token=env.TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

# /start handler
startHandler = StartHandler(dispatcher)
startHandler.add_to_dispatcher()

# /place handler
placeTaskListHandler = TaskListHandler('place', 'placeTaskInstances', 'Place', dispatcher)
placeTaskListHandler.add_to_dispatcher()

# /food handler
foodTaskListHandler = TaskListHandler('food', 'foodTaskInstances', 'Food', dispatcher)
foodTaskListHandler.add_to_dispatcher()

# /course handler
courseTaskListHandler = TaskListHandler('course', 'questionTaskInstances', 'Question', dispatcher)
courseTaskListHandler.add_to_dispatcher()

# /trashbin handler
trashBinTaskListHandler = TaskListHandler('trashbin', 'trashBinTaskInstances', 'Trash Bin', dispatcher)
trashBinTaskListHandler.add_to_dispatcher()

updater.start_webhook(listen='0.0.0.0', port=env.PORT, url_path=env.TELEGRAM_BOT_TOKEN, webhook_url=env.NGROK_CAMPUSBOT_URL+'/'+env.TELEGRAM_BOT_TOKEN)
updater.bot.set_webhook(env.NGROK_CAMPUSBOT_URL+'/'+env.TELEGRAM_BOT_TOKEN)
updater.idle()