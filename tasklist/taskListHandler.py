from telegram.ext import Updater, CommandHandler, Filters
from telegram import ChatAction
import db.firestoreClient as FirestoreClient
from db.user import User
from db.taskInstance import TaskInstance
from dialoguemanager.response.generalCopywriting import START_MESSAGE, LOADING_TASKS_TEXT
from dialoguemanager.response.taskListCopywriting import SELECT_TASK_INSTRUCTION, NO_TASK_INSTANCES_AVAILABLE
from flowhandler.createFlowHandler import CreateFlowHandler
from flowhandler.enrichFlowHandler import EnrichFlowHandler
from flowhandler.validateFlowHandler import ValidateFlowHandler
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
        self.handlersPerUser = {}
        self.cleanCanonicalName = self.canonicalName.lower().replace(" ", "")

    def add_to_dispatcher(self):
        self.dispatcher.add_handler(self.entryCommandHandler)
        self.load_task_list_persistence()
        pprint(self.handlersPerUser)

    def build_task_list_message(self, user, update, context):
        taskInstances = TaskInstance.get_task_instances_for_user(user, taskInstanceCollectionName=self.taskInstanceCollectionName)
        messages = []
        context.chat_data['tasks'] = {}

        for idx,taskInstance in enumerate(taskInstances):
            # build message
            taskPreview = taskInstance['task_preview']
            task = taskInstance.task
            item = task['item']
            command = "{entryCommand}{idx}".format(entryCommand=self.cleanCanonicalName, idx=idx+1)
            preview_url = "http://campusbot.cf/task-preview?title={taskPreview[title]}&imageurl={taskPreview[imageurl]}&itemtype={taskPreview[itemtype]}&description={taskPreview[description]}".format(
                taskPreview=taskPreview,
                canonicalName=self.canonicalName
            )
            message = u"/{command} <b>{taskPreview[caption]}</b><a href='{preview_url}'>\u200f</a>".format(command=command, taskPreview=taskPreview, preview_url=preview_url)
            messages.append(message)
            # add command handler to dispatcher for this user
            if task['type'] == taskType.TASK_TYPE_ENRICH_ITEM:
                flowHandler = EnrichFlowHandler(self.cleanCanonicalName, self.enrichmentCollectionName, self.dispatcher, command, taskInstance)
            elif task['type'] == taskType.TASK_TYPE_VALIDATE_ITEM:
                flowHandler = ValidateFlowHandler(self.cleanCanonicalName, self.validationCollectionName, self.dispatcher, command, taskInstance)
        
            flowHandler.add_to_dispatcher(user)
            self.handlersPerUser[user['telegramId']].append(flowHandler.conversationHandler)

            context.chat_data['tasks'][command] = taskInstance
        return messages

    def load_task_list_persistence(self):
        chat_data = FirestoreClient.getCollection('botChatData', asDict=True)
        if chat_data is not None:
            for chatId in chat_data:
                user = chat_data[chatId]['user']
                if 'tasks' in chat_data[chatId]:
                    # add create command handler
                    self.createFlowHandler.add_to_dispatcher(user)
                    self.handlersPerUser[user['telegramId']] = [self.createFlowHandler]

                    taskInstances = chat_data[chatId]['tasks']
                    for command,taskInstance in taskInstances.items():
                        # only add if this is the corresponding task list handler
                        if command.startswith(self.entryCommand):
                            task = taskInstance['task']
                            if task['type'] == taskType.TASK_TYPE_ENRICH_ITEM:
                                flowHandler = EnrichFlowHandler(self.cleanCanonicalName, self.enrichmentCollectionName, self.dispatcher, command, taskInstance)
                            elif task['type'] == taskType.TASK_TYPE_VALIDATE_ITEM:
                                flowHandler = ValidateFlowHandler(self.cleanCanonicalName, self.validationCollectionName, self.dispatcher, command, taskInstance)
                        
                            flowHandler.add_to_dispatcher(user)
                            self.handlersPerUser[user['telegramId']].append(flowHandler.conversationHandler)



    def _entry_command_callback(self, update, context):
        # don't show list if they are currently in the middle of a task
        if 'currentTaskInstance' in context.chat_data:
            return
            
        bot = context.bot
        chatId = update.message.chat_id
        bot.send_message(chat_id=chatId, text=LOADING_TASKS_TEXT, parse_mode='Markdown')

        userTelegramId = unicode(update.message.from_user.id)
        context.chat_data['user'] = User.getUserById(userTelegramId)
        user = context.chat_data['user']
        # clean command handlers
        if userTelegramId in self.handlersPerUser:
            for handler in self.handlersPerUser[userTelegramId]:
                self.dispatcher.remove_handler(handler)
        self.createFlowHandler.add_to_dispatcher(user)
        self.handlersPerUser[userTelegramId] = [self.createFlowHandler]

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
        for handler in self.handlersPerUser[context.chat_data['user']['telegramId']]:
            self.dispatcher.remove_handler(handler)
        self.handlersPerUser[context.chat_data['user']['telegramId']] = []
                
        
