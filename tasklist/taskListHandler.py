from telegram.ext import Updater, CommandHandler, Filters
from telegram import ChatAction
import db.firestoreClient as FirestoreClient
from db.user import User
from db.taskInstance import TaskInstance
from dialoguemanager.response.generalCopywriting import START_MESSAGE, LOADING_TASKS_TEXT, INSTRUCTION_TO_QUIT_TASK_TEXT
from dialoguemanager.response.taskListCopywriting import SELECT_TASK_INSTRUCTION, NO_TASK_INSTANCES_AVAILABLE
from flowhandler.createFlowHandler import CreateFlowHandler
from flowhandler.enrichFlowHandler import EnrichFlowHandler
from flowhandler.validateFlowHandler import ValidateFlowHandler
from pprint import pprint
from common.constants import taskType
from persistence.handlersPerUser import handlersPerUser

class TaskListHandler:

    def __init__(self, entryCommand, taskInstanceCollectionName, canonicalName, dispatcher, itemCollectionNamePrefix=''):
        self.dispatcher = dispatcher
        self.taskInstanceCollectionName = taskInstanceCollectionName
        self.canonicalName = canonicalName
        self.entryCommand = entryCommand
        self.itemCollectionName = '{prefix}Items'.format(prefix=itemCollectionNamePrefix)
        self.enrichmentCollectionName = '{prefix}Enrichments'.format(prefix=itemCollectionNamePrefix)
        self.validationCollectionName = '{prefix}Validations'.format(prefix=itemCollectionNamePrefix)
        self.prefix = itemCollectionNamePrefix
        # create a command handler for entry
        self.entryCommandHandler = CommandHandler(entryCommand, self._entry_command_callback)
        # create a command handler to create new item
        self.cleanCanonicalName = self.canonicalName.lower().replace(" ", "")
        self.createFlowHandler = CreateFlowHandler(self.cleanCanonicalName, self.itemCollectionName, dispatcher, itemCollectionNamePrefix)

    def add_to_dispatcher(self):
        self.dispatcher.add_handler(self.entryCommandHandler)
        self.load_task_list_persistence()

    def build_task_list_message(self, user, update, context):
        taskInstances = TaskInstance.get_task_instances_for_user(user, taskInstanceCollectionName=self.taskInstanceCollectionName)
        messages = []
        context.chat_data['tasks'] = {}

        # add refresh handler
        self.add_refresh_command_handler(user)
        offset = context.chat_data.get('task_list_offset', 0)
        if offset >= len(taskInstances):
            offset = 0
            context.chat_data['task_list_offset'] = 0

        for idx,taskInstance in enumerate(taskInstances[offset:offset+5]):
            # build message
            taskPreview = taskInstance['task_preview']
            task = taskInstance.task
            item = task['item']
            command = "{entryCommand}{idx}".format(entryCommand=self.cleanCanonicalName, idx=idx+1+offset)
            preview_url = "http://campusbot.cf/task-preview?title={taskPreview[title]}&imageurl={taskPreview[imageurl]}&itemtype={taskPreview[itemtype]}&description={taskPreview[description]}".format(
                taskPreview=taskPreview,
                canonicalName=self.canonicalName
            )
            message = u"/{command} <b>{taskPreview[caption]}</b><a href='{preview_url}'>\u200f</a>".format(command=command, taskPreview=taskPreview, preview_url=preview_url)
            messages.append(message)
            # add command handler to dispatcher for this user
            if task['type'] == taskType.TASK_TYPE_ENRICH_ITEM:
                flowHandler = EnrichFlowHandler(self.cleanCanonicalName, self.enrichmentCollectionName, self.dispatcher, command, taskInstance, self.prefix)
            elif task['type'] == taskType.TASK_TYPE_VALIDATE_ITEM:
                flowHandler = ValidateFlowHandler(self.cleanCanonicalName, self.validationCollectionName, self.dispatcher, command, taskInstance, self.prefix)
        
            flowHandler.add_to_dispatcher(user)
            handlersPerUser[user['telegramId']].append(flowHandler.conversationHandler)

            context.chat_data['tasks'][command] = taskInstance

        return messages

    def load_task_list_persistence(self):
        chat_data = FirestoreClient.getCollection('botChatData', asDict=True)
        if chat_data is not None:
            for chatId in chat_data:
                user_chat_data = chat_data[chatId]
                user = user_chat_data['user']
                if 'tasks' in user_chat_data:
                    # add create command handler
                    if 'current_task_list' in user_chat_data and self.canonicalName == user_chat_data['current_task_list']: 
                        self.createFlowHandler.add_to_dispatcher(user)
                        handlersPerUser[user['telegramId']] = [self.createFlowHandler.conversationHandler]

                        # add refresh handler
                        self.add_refresh_command_handler(user)

                        taskInstances = user_chat_data['tasks']
                        for command,taskInstance in taskInstances.items():
                            task = taskInstance['task']
                            if task['type'] == taskType.TASK_TYPE_ENRICH_ITEM:
                                flowHandler = EnrichFlowHandler(self.cleanCanonicalName, self.enrichmentCollectionName, self.dispatcher, command, taskInstance, self.prefix)
                            elif task['type'] == taskType.TASK_TYPE_VALIDATE_ITEM:
                                flowHandler = ValidateFlowHandler(self.cleanCanonicalName, self.validationCollectionName, self.dispatcher, command, taskInstance, self.prefix)
                        
                            flowHandler.add_to_dispatcher(user)
                            handlersPerUser[user['telegramId']].append(flowHandler.conversationHandler)

    def _entry_command_callback(self, update, context):
        userTelegramId = unicode(update.message.from_user.id)
        chat = update.message.chat
        userDetails = {}

        if hasattr(chat, 'username'):
            userDetails['username'] = chat.username

        if hasattr(chat, 'first_name'):
            userDetails['firstName'] = chat.first_name
        
        if hasattr(chat, 'last_name'):
            userDetails['lastName'] = chat.last_name

        context.chat_data['user'] = User.getUserById(userTelegramId, userDetails)

        User.saveUtterance(userTelegramId, update.message)

        bot = context.bot
        chatId = update.message.chat_id
        
        # don't show list if they are currently in the middle of a task
        if 'currentTaskInstance' in context.chat_data:
            message = bot.send_message(chat_id=chatId, text=INSTRUCTION_TO_QUIT_TASK_TEXT, parse_mode='Markdown')
            User.saveUtterance(userTelegramId, message, byBot=True)
            return

        message = bot.send_message(chat_id=chatId, text=LOADING_TASKS_TEXT, parse_mode='Markdown')
        User.saveUtterance(userTelegramId, message, byBot=True)
        
        user = context.chat_data['user']
        # clean command handlers
        if userTelegramId in handlersPerUser:
            for handler in handlersPerUser[userTelegramId]:
                self.dispatcher.remove_handler(handler)
        self.createFlowHandler.add_to_dispatcher(user)
        handlersPerUser[userTelegramId] = [self.createFlowHandler.conversationHandler]
        context.chat_data['current_task_list'] = unicode(self.canonicalName)
        # reset task offset
        context.chat_data['task_list_offset'] = 0

        self.send_task_list_message(update, context)
        
    def send_task_list_message(self, update, context): 
        userTelegramId = unicode(update.message.from_user.id)
        bot = context.bot
        chatId = update.message.chat_id
        user = context.chat_data['user']
        bot.send_chat_action(chatId, ChatAction.TYPING)
        messageOfTaskInstances = self.build_task_list_message(user, update, context)
        for message in messageOfTaskInstances:
            bot.send_chat_action(chatId, ChatAction.TYPING)
            message = bot.send_message(chat_id=chatId, text=message,parse_mode='HTML')
            User.saveUtterance(userTelegramId, message, byBot=True)

        if not messageOfTaskInstances:
            message = bot.send_message(chat_id=chatId, text=NO_TASK_INSTANCES_AVAILABLE.format(canonicalName=self.canonicalName), parse_mode='Markdown')
            User.saveUtterance(userTelegramId, message, byBot=True)
            message = bot.send_message(chat_id=chatId, text=START_MESSAGE, parse_mode='Markdown')
            User.saveUtterance(userTelegramId, message, byBot=True)
        else:
            message = bot.send_message(chat_id=chatId, text=SELECT_TASK_INSTRUCTION.format(canonicalName=self.canonicalName), parse_mode='Markdown')
            User.saveUtterance(userTelegramId, message, byBot=True)

    def _refresh_command_callback(self, update, context):
        userTelegramId = unicode(update.message.from_user.id)
        User.saveUtterance(userTelegramId, update.message)

        context.chat_data['task_list_offset'] = context.chat_data.get('task_list_offset', 0) + 5
        self.send_task_list_message(update, context)

    def add_refresh_command_handler(self, user):
        # add refresh handler
        refreshCommandHandler = CommandHandler("refresh", self._refresh_command_callback, filters=Filters.user(int(user['telegramId'])))
        self.dispatcher.add_handler(refreshCommandHandler)
        handlersPerUser[user['telegramId']].append(refreshCommandHandler)
                
        
