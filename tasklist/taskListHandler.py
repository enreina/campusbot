from telegram.ext import Updater, CommandHandler
from db.user import User

class TaskListHandler:

    def __init__(self, entry_command, task_instance_collection_name, canonical_name, dispatcher):
        self.dispatcher = dispatcher
        self.task_instance_collection_name = task_instance_collection_name
        self.canonical_name = canonical_name
        # create a command handler for entry
        self.entry_command_handler = CommandHandler(entry_command, self._entry_command_callback)
        self.dispatcher.add_handler(self.entry_command_handler)


    def _entry_command_callback(self, update, context):
        bot = context.bot
        chatId = update.message.chat_id
        userTelegramId = unicode(update.message.from_user.id)

        # to do, implement to send list of tasks
        bot.send_message(chat_id=chatId, text=u"/place1 <b>TU Delft Library</b> <a href='http://campusbot.cf/task-preview?title=Validate&imageurl=https://d1rkab7tlqy5f1.cloudfront.net/_processed_/2/7/csm_Contactinfo%20gebouw%20buitenkant_54b704d5fa.jpg&itemtype=Place'>\u200f</a>",parse_mode='HTML')
        
        context.chat_data['user'] = User.getUserById(userTelegramId)
