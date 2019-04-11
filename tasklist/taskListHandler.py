from telegram.ext import Updater, CommandHandler, Filters
from telegram import ChatAction
from db.user import User
from db.taskInstance import TaskInstance
from dialoguemanager.response.generalCopywriting import START_MESSAGE
from dialoguemanager.response.taskListCopywriting import SELECT_TASK_INSTRUCTION, NO_TASK_INSTANCES_AVAILABLE
from flowhandler.createFlowHandler import CreateFlowHandler
from flowhandler.enrichFlowHandler import EnrichFlowHandler
from pprint import pprint
from common.constants import taskType

class TaskListHandler:

    def __init__(self, entryCommand, taskInstanceCollectionName, canonicalName, dispatcher, itemCollectionNamePrefix=''):
        self.dispatcher = dispatcher
        self.taskInstanceCollectionName = taskInstanceCollectionName
        self.canonicalName = canonicalName
        self.entryCommand = entryCommand
        self.itemCollectionName = '{prefix}Items'.format(prefix=itemCollectionNamePrefix)
        self.enrichmentCollectionName = '{prefix}Enrichments'.format(prefix=itemCollectionNamePrefix)
        self.validationCollectionName = '{prefix}Validations'.format(prefix=itemCollectionNamePrefix)
        # create a command handler for entry
        self.entryCommandHandler = CommandHandler(entryCommand, self._entry_command_callback)
        # create a command handler to create new item
        self.createFlowHandler = CreateFlowHandler(entryCommand, self.itemCollectionName, dispatcher)

    def add_to_dispatcher(self):
        self.dispatcher.add_handler(self.entryCommandHandler)

    def build_task_list_message(self, user, update, context):
        taskInstances = TaskInstance.get_task_instances_for_user(user, taskInstanceCollectionName=self.taskInstanceCollectionName)
        messages = []
        context.chat_data['tasks'] = {}

        for idx,taskInstance in enumerate(taskInstances):
            # build message
            taskPreview = taskInstance['task_preview']
            task = taskInstance.task
            item = task['item']
            cleanCanonicalName = self.canonicalName.lower().replace(" ", "")
            command = "{entryCommand}{idx}".format(entryCommand=cleanCanonicalName, idx=idx+1)
            preview_url = "http://campusbot.cf/task-preview?title={taskPreview[title]}&imageurl={taskPreview[imageurl]}&itemtype={taskPreview[itemtype]}&description={taskPreview[description]}".format(
                taskPreview=taskPreview,
                canonicalName=self.canonicalName
            )
            message = u"/{command} <b>{taskPreview[caption]}</b><a href='{preview_url}'>\u200f</a>".format(command=command, taskPreview=taskPreview, preview_url=preview_url)
            messages.append(message)
            # add command handler to dispatcher for this user
            if task['type'] == taskType.TASK_TYPE_ENRICH_ITEM:
                flowHandler = EnrichFlowHandler(cleanCanonicalName, self.enrichmentCollectionName, self.dispatcher, command, taskInstance)
                flowHandler.add_to_dispatcher(user)
                context.chat_data['handlers'].append(flowHandler.conversationHandler)

            context.chat_data['tasks'][command] = taskInstance
        return messages

    def _entry_command_callback(self, update, context):
        bot = context.bot
        chatId = update.message.chat_id
        userTelegramId = unicode(update.message.from_user.id)
        context.chat_data['user'] = User.getUserById(userTelegramId)
        user = context.chat_data['user']
        # don't show list if they are currently in the middle of a task
        if 'currentTaskInstance' in context.chat_data:
            return
        # clean command handlers
        if 'handlers' in context.chat_data:
            for handler in context.chat_data['handlers']:
                self.dispatcher.remove_handler(handler)
        context.chat_data['handlers'] = []
        self.createFlowHandler.add_to_dispatcher(user)

        bot.send_chat_action(chatId, ChatAction.TYPING)
        # to do, implement to send list of tasks
        messageOfTaskInstances = self.build_task_list_message(user, update, context)
        for message in messageOfTaskInstances:
            bot.send_chat_action(chatId, ChatAction.TYPING)
            bot.send_message(chat_id=chatId, text=message,parse_mode='HTML')
        
        if not messageOfTaskInstances:
            bot.send_message(chat_id=chatId, text=NO_TASK_INSTANCES_AVAILABLE.format(canonicalName=self.canonicalName), parse_mode='Markdown')
            bot.send_message(chat_id=chatId, text=START_MESSAGE, parse_mode='Markdown')
        else:
            bot.send_message(chat_id=chatId, text=SELECT_TASK_INSTRUCTION.format(canonicalName=self.canonicalName), parse_mode='Markdown')

    def _select_task_callback(self, update, context):
        for entity in update.message.entities:
            if entity.type == 'bot_command':
                command = update.message.text[entity.offset+1:entity.offset+entity.length]
                break
        taskInstance = context.chat_data['tasks'][command]
        
        # TO-DO create task executioner
        context.bot.send_message(chat_id=update.message.chat_id, text="You have selected *{taskTitle}*".format(taskTitle=taskInstance.title), parse_mode='Markdown')

        # clean command handlers
        for handler in context.chat_data['handlers']:
            self.dispatcher.remove_handler(handler)
                
        
