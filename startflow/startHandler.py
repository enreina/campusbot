from telegram.ext import Updater, CommandHandler, ConversationHandler
from db.user import User
from dialoguemanager.response import generalCopywriting

class StartHandler:

    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        # create a command handler for entry
        self.start_command_handler = CommandHandler('start', self._start_callback)
        self.help_command_handler = CommandHandler('help', self._help_callback)
        
    def add_to_dispatcher(self):
        self.dispatcher.add_handler(self.start_command_handler)
        self.dispatcher.add_handler(self.help_command_handler)

    def _start_callback(self, update, context):
        bot = context.bot
        chatId = update.message.chat_id
        userTelegramId = unicode(update.message.from_user.id)

        if 'currentTaskInstance' in context.chat_data:
            message = bot.send_message(chat_id=chatId, text=generalCopywriting.INSTRUCTION_TO_QUIT_TASK_TEXT, parse_mode='Markdown')
            User.saveUtterance(userTelegramId, message, byBot=True)
            return

        #save user message
        User.saveUtterance(userTelegramId, update.message)

        message = context.bot.send_message(chat_id=chatId, text=generalCopywriting.WELCOME_MESSAGE, parse_mode='Markdown')
        User.saveUtterance(userTelegramId, message, byBot=True)
        message = context.bot.send_message(chat_id=chatId, text=generalCopywriting.START_MESSAGE, parse_mode='Markdown')
        User.saveUtterance(userTelegramId, message, byBot=True)

        context.chat_data['user'] = User.getUserById(userTelegramId)

    def _help_callback(self, update, context):
        bot = context.bot
        chatId = update.message.chat_id
        userTelegramId = unicode(update.message.from_user.id)

        #save user message
        User.saveUtterance(userTelegramId, update.message)

        message = context.bot.send_message(chat_id=chatId, text=generalCopywriting.HELP_MESSAGE, parse_mode='Markdown')
        User.saveUtterance(userTelegramId, message, byBot=True)
        

