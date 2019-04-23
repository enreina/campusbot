from telegram.ext import Updater, CommandHandler
from db.user import User
from dialoguemanager.response import generalCopywriting

class StartHandler:

    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        # create a command handler for entry
        self.start_command_handler = CommandHandler('start', self._start_callback)

    def add_to_dispatcher(self):
        self.dispatcher.add_handler(self.start_command_handler)

    def _start_callback(self, update, context):
        bot = context.bot
        chatId = update.message.chat_id
        userTelegramId = unicode(update.message.from_user.id)

        context.bot.send_message(chat_id=chatId, text=generalCopywriting.WELCOME_MESSAGE, parse_mode='Markdown')
        context.bot.send_message(chat_id=chatId, text=generalCopywriting.START_MESSAGE, parse_mode='Markdown')

        context.chat_data['user'] = User.getUserById(userTelegramId)

