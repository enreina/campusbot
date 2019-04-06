from telegram.ext import Updater, CommandHandler
from db.user import User
from db.taskInstance import TaskInstance
from pprint import pprint
from dialoguemanager.response.generalCopywriting import NO_TASK_INSTANCES_AVAILABLE, START_MESSAGE

class TaskListHandler:

    def __init__(self, entry_command, task_instance_collection_name, canonical_name, dispatcher):
        self.dispatcher = dispatcher
        self.task_instance_collection_name = task_instance_collection_name
        self.canonical_name = canonical_name
        self.entry_command = entry_command
        # create a command handler for entry
        self.entry_command_handler = CommandHandler(entry_command, self._entry_command_callback)

    def add_to_dispatcher(self):
        self.dispatcher.add_handler(self.entry_command_handler)

    def build_task_list_message(self, user):
        taskInstances = TaskInstance.get_task_instances_for_user(user, task_instance_collection_name=self.task_instance_collection_name)
        messages = []
        for idx,taskInstance in enumerate(taskInstances):
            # build message
            taskInstanceTitle = taskInstance.title
            task = taskInstance.task
            item = task['item']
            command = "/{entry_command}{idx}".format(entry_command=self.entry_command, idx=idx+1)
            preview_url = "http://campusbot.cf/task-preview?title={taskTypeAsString}&imageurl={item[image]}&itemtype={canonical_name}".format(
                taskTypeAsString=taskInstance.taskTypeAsString,
                item=item,
                canonical_name=self.canonical_name
            )
            message = u"{command} <b>{title}</b><a href='{preview_url}'>\u200f</a>".format(command=command, title=taskInstanceTitle, preview_url=preview_url)
            messages.append(message)

        return messages

    def _entry_command_callback(self, update, context):
        bot = context.bot
        chatId = update.message.chat_id
        userTelegramId = unicode(update.message.from_user.id)
        context.chat_data['user'] = User.getUserById(userTelegramId)
        user = context.chat_data['user']

        # to do, implement to send list of tasks
        messageOfTaskInstances = self.build_task_list_message(user)
        for message in messageOfTaskInstances:
            bot.send_message(chat_id=chatId, text=message,parse_mode='HTML')
        
        if not messageOfTaskInstances:
            bot.send_message(chat_id=chatId, text=NO_TASK_INSTANCES_AVAILABLE.format(canonical_name=self.canonical_name), parse_mode='Markdown')
            bot.send_message(chat_id=chatId, text=START_MESSAGE, parse_mode='Markdown')
        
