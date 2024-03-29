from telegram.ext import Updater, CommandHandler, MessageHandler
import logging
import settings as env
from dialoguemanager.response import generalCopywriting
from tasklist.taskListHandler import TaskListHandler
from startflow.startHandler import StartHandler
from persistence.campusBotPersistence import CampusBotPersistence

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

if env.MAINTENANCE_MODE:
    updater = Updater(token=env.TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    def _maintenance_callback(update, context):
        update.message.reply_text(generalCopywriting.MAINTENANCE_MODE_TEXT)
    maintenanceHandler = MessageHandler(filters=None, callback=_maintenance_callback)
    dispatcher.add_handler(maintenanceHandler)
else:
    # create persistence file
    persistenceObject = CampusBotPersistence()

    updater = Updater(token=env.TELEGRAM_BOT_TOKEN, persistence=persistenceObject, use_context=True)
    dispatcher = updater.dispatcher

    # /start handler
    startHandler = StartHandler(dispatcher)
    startHandler.add_to_dispatcher()

    # /place handler
    placeTaskListHandler = TaskListHandler('place', 'placeTaskInstances', 'Place', dispatcher, 'place')
    placeTaskListHandler.add_to_dispatcher()

    # /food handler
    foodTaskListHandler = TaskListHandler('food', 'foodTaskInstances', 'Food', dispatcher, 'food')
    foodTaskListHandler.add_to_dispatcher()

    # /course handler
    courseTaskListHandler = TaskListHandler('course', 'questionTaskInstances', 'Question', dispatcher, 'question')
    courseTaskListHandler.add_to_dispatcher()

    # /trashbin handler
    trashBinTaskListHandler = TaskListHandler('trashbin', 'trashBinTaskInstances', 'Trash Bin', dispatcher, 'trashBin')
    trashBinTaskListHandler.add_to_dispatcher()

updater.start_webhook(listen='0.0.0.0', port=env.PORT, url_path=env.TELEGRAM_BOT_TOKEN, webhook_url=env.NGROK_CAMPUSBOT_URL+'/'+env.TELEGRAM_BOT_TOKEN)
updater.bot.set_webhook(env.NGROK_CAMPUSBOT_URL+'/'+env.TELEGRAM_BOT_TOKEN)
logger.info("CampusBot is ready")
updater.idle()

