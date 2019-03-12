from telegram.ext import Updater, CommandHandler
import logging
import settings as env
from dialoguemanager.response import generalCopywriting
from hc.taskExecutioner import TaskExecutioner

updater = Updater(token=env.TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

## command handlers
def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text=generalCopywriting.WELCOME_MESSAGE, parse_mode='Markdown')
                
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

createPlaceExecutioner = TaskExecutioner('create-place')
dispatcher.add_handler(createPlaceExecutioner.conversationHandler)

validatePlaceExecutioner = TaskExecutioner('validate-place')
dispatcher.add_handler(validatePlaceExecutioner.conversationHandler)

categorizePlaceExecutioner = TaskExecutioner('categorize-place')
dispatcher.add_handler(categorizePlaceExecutioner.conversationHandler)

enrichPlaceExecutioner = TaskExecutioner('enrich-place')
dispatcher.add_handler(enrichPlaceExecutioner.conversationHandler)

createMealExecutioner = TaskExecutioner('create-meal')
dispatcher.add_handler(createMealExecutioner.conversationHandler)

updater.start_webhook(listen='0.0.0.0', port=env.PORT, url_path=env.TELEGRAM_BOT_TOKEN, webhook_url=env.NGROK_CAMPUSBOT_URL+'/'+env.TELEGRAM_BOT_TOKEN)
updater.bot.set_webhook(env.NGROK_CAMPUSBOT_URL+'/'+env.TELEGRAM_BOT_TOKEN)
updater.idle()