from telegram.ext import Updater, CommandHandler, ConversationHandler, CallbackQueryHandler
from db.user import User
from dialoguemanager.response import generalCopywriting

class StartHandler:

    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        # create a command handler for entry
        self.start_command_handler = CommandHandler('start', self._start_callback)
        self.help_command_handler = CommandHandler('help', self._help_callback)
        self.push_notif_callbackquery_handler = CallbackQueryHandler(self._push_notif_handler, pattern=generalCopywriting.PUSH_NOTIF_RESPONSE_PATTERN)
        
    def add_to_dispatcher(self):
        self.dispatcher.add_handler(self.start_command_handler)
        self.dispatcher.add_handler(self.help_command_handler)
        self.dispatcher.add_handler(self.push_notif_callbackquery_handler)

    def _start_callback(self, update, context):
        bot = context.bot
        chatId = update.message.chat_id
        userTelegramId = unicode(update.message.from_user.id)
        chat = update.message.chat
        userDetails = {}

        if hasattr(chat, 'username'):
            userDetails['username'] = chat.username

        if hasattr(chat, 'first_name'):
            userDetails['firstName'] = chat.first_name
        
        if hasattr(chat, 'last_name'):
            userDetails['lastName'] = chat.last_name

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

        context.chat_data['user'] = User.getUserById(userTelegramId, userDetails=userDetails)

    def _help_callback(self, update, context):
        bot = context.bot
        chatId = update.message.chat_id
        userTelegramId = unicode(update.message.from_user.id)

        #save user message
        User.saveUtterance(userTelegramId, update.message)

        message = context.bot.send_message(chat_id=chatId, text=generalCopywriting.HELP_MESSAGE, parse_mode='Markdown')
        User.saveUtterance(userTelegramId, message, byBot=True)

    def _push_notif_handler(self, update, context):
        bot = context.bot
        chatId = update.callback_query.message.chat_id
        messageId = update.callback_query.message.chat_id.message_id
        userTelegramId = unicode(update.callback_query.message.chat_id)
        bot.answer_callback_query(update.callback_query.id)
        edit_message_reply_markup(chat_id=chatId, message_id=messageId, reply_markup=None)
        
        user = User.getUserById(userTelegramId)
        context.chat_data['user'] = user

        if not user.get('hasReceivedPushNotif', False):
            return
        else:
            User.updateUser(user['_id'], {'hasReceivedPushNotif': False})

        if 'currentTaskInstance' in context.chat_data:
            message = bot.send_message(chat_id=chatId, text=generalCopywriting.INSTRUCTION_TO_QUIT_TASK_TEXT, parse_mode='Markdown')
            User.saveUtterance(userTelegramId, message, byBot=True)
            return

        if update.callback_query.data == generalCopywriting.PUSH_NOTIF_RESPONSE_YES_CALLBACK:
            message = context.bot.send_message(chat_id=chatId, text=generalCopywriting.START_MESSAGE, parse_mode='Markdown')
            User.saveUtterance(userTelegramId, message, byBot=True)
        else:
            message = context.bot.send_message(chat_id=chatId, text=generalCopywriting.PUSH_NOTIF_RESPONSE_FOR_NO, parse_mode='Markdown')
            User.saveUtterance(userTelegramId, message, byBot=True)
        

