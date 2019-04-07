from telegram.ext import Updater, CommandHandler, Filters
from telegram import ChatAction
from db.user import User
from db.taskInstance import TaskInstance
from dialoguemanager.response.generalCopywriting import START_MESSAGE
from dialoguemanager.response.taskListCopywriting import SELECT_TASK_INSTRUCTION, NO_TASK_INSTANCES_AVAILABLE

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

    def build_task_list_message(self, user, update, context):
        taskInstances = TaskInstance.get_task_instances_for_user(user, task_instance_collection_name=self.task_instance_collection_name)
        messages = []
        context.chat_data['tasks'] = {}
        context.chat_data['commandHandlers'] = []

        for idx,taskInstance in enumerate(taskInstances):
            # build message
            taskInstanceTitle = taskInstance.title
            task = taskInstance.task
            item = task['item']
            command = "{entry_command}{idx}".format(entry_command=self.entry_command, idx=idx+1)
            preview_url = "http://campusbot.cf/task-preview?title={taskTypeAsString}&imageurl={item[image]}&itemtype={canonical_name}".format(
                taskTypeAsString=taskInstance.taskTypeAsString,
                item=item,
                canonical_name=self.canonical_name
            )
            message = u"/{command} <b>{title}</b><a href='{preview_url}'>\u200f</a>".format(command=command, title=taskInstanceTitle, preview_url=preview_url)
            messages.append(message)
            # add command handler to dispatcher for this user
            selectTaskCommandHandler = CommandHandler(command, self._select_task_callback, filters=Filters.user(int(user['telegramId'])))
            self.dispatcher.add_handler(selectTaskCommandHandler)
            context.chat_data['commandHandlers'].append(selectTaskCommandHandler)

            context.chat_data['tasks'][command] = taskInstance
        return messages

    def _entry_command_callback(self, update, context):
        bot = context.bot
        chatId = update.message.chat_id
        userTelegramId = unicode(update.message.from_user.id)
        context.chat_data['user'] = User.getUserById(userTelegramId)
        user = context.chat_data['user']

        bot.send_chat_action(chatId, ChatAction.TYPING)
        # to do, implement to send list of tasks
        messageOfTaskInstances = self.build_task_list_message(user, update, context)
        for message in messageOfTaskInstances:
            bot.send_chat_action(chatId, ChatAction.TYPING)
            bot.send_message(chat_id=chatId, text=message,parse_mode='HTML')
        
        if not messageOfTaskInstances:
            bot.send_message(chat_id=chatId, text=NO_TASK_INSTANCES_AVAILABLE.format(canonical_name=self.canonical_name), parse_mode='Markdown')
            bot.send_message(chat_id=chatId, text=START_MESSAGE, parse_mode='Markdown')
        else:
            bot.send_message(chat_id=chatId, text=SELECT_TASK_INSTRUCTION.format(canonical_name=self.canonical_name), parse_mode='Markdown')

    def _select_task_callback(self, update, context):
        for entity in update.message.entities:
            if entity.type == 'bot_command':
                command = update.message.text[entity.offset+1:entity.offset+entity.length]
                break
        taskInstance = context.chat_data['tasks'][command]
        
        # TO-DO create task executioner
        context.bot.send_message(chat_id=update.message.chat_id, text="You have selected *{taskTitle}*".format(taskTitle=taskInstance.title), parse_mode='Markdown')

        # clean command handlers
        for handler in context.chat_data['commandHandlers']:
            self.dispatcher.remove_handler(handler)
                
        
