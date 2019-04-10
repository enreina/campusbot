from db.taskTemplate import TaskTemplate
from db.item import Item
from db.category import Category
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from dialoguemanager.response import generalCopywriting
import db.firestoreClient as FirestoreClient
from common.placeUtility import findNearestBuilding
from common.constants import taskType, questionType, specialStates, callbackTypes
from client.telegramClient import dispatcher
from pprint import pprint
from common.inlineKeyboardHelper import buildInlineKeyboardMarkup
from common import logicJumpHelper
import re
from datetime import datetime
from dateutil.tz import tzlocal
import settings as env
import json

class GenericFlowHandler(object):
    '''Abstraction of a task flow handler

    Attributes:
        taskTemplate: the task tempalate data loaded from database
        dispatcher: the dispatcher used by telegram bot api
    '''

    def __init__(self, taskTemplateId, dispatcher, itemCollectionName='items'):
        self.taskTemplate = TaskTemplate.getTaskTemplateById(taskTemplateId) # load task from db
        self.dispatcher = dispatcher
        self.itemCollectionName = itemCollectionName

    def init_conversation_handler(self, user):
        # entry points
        entryPoints = [CommandHandler(self.taskTemplate.entryCommand, self._start_task_callback, filters=Filters.user(int(user['telegramId'])))]
        # create states
        states = {}

        for questionNumber, question in enumerate(self.taskTemplate.questions):
            # create handler
            handler = []
            if question['type'] == questionType.QUESTION_TYPE_IMAGE:
                handler.append(MessageHandler(Filters.photo, self._question_callback))
            elif question['type'] == questionType.QUESTION_TYPE_LOCATION:
                handler.append(MessageHandler(Filters.location, self._question_callback))
            elif question['type'] == questionType.QUESTION_TYPE_NUMBER:
                handler.append(MessageHandler(Filters.regex(r'^[0-9]*$'), self._question_callback))
            elif question['type'] in questionType.TEXT_BASED_QUESTION_TYPES:
                handler.append(MessageHandler(Filters.text, self._question_callback))
            elif question['type'] in questionType.INLINE_BUTTON_BASED_QUESTION_TYPES:
                handler.append(CallbackQueryHandler(self._question_callback))
            
            if question['type'] == questionType.QUESTION_TYPE_BUILDING_ITEM:
                handler.append(MessageHandler(Filters.text, self._question_callback))
            
            states[questionNumber] = handler
        self.numOfStates = len(self.taskTemplate.questions)
        self.conversationHandler = ConversationHandler(entry_points=entryPoints, states=states, fallbacks=[MessageHandler(Filters.all, self._fallbackCallback)])

    def add_to_dispatcher(self, user):
        self.init_conversation_handler(user)
        self.dispatcher.add_handler(self.conversationHandler)
    
    def send_current_question(self, update, context):
        bot = context.bot
        temporaryAnswer = context.chat_data['temporaryAnswer']
        
        if 'currentQuestionNumber' in context.chat_data:
            currentQuestionNumber = context.chat_data['currentQuestionNumber']
        else:
            currentQuestionNumber = 0

        if update.callback_query:
            chatId = update.callback_query.message.chat_id
        else:
            chatId = update.message.chat_id

        currentQuestion = self.taskTemplate.questions[currentQuestionNumber]
        formattedQuestion = currentQuestion['text'].format(item=temporaryAnswer)

        if currentQuestion['type'] == questionType.QUESTION_TYPE_LOCATION:
            replyMarkup = {"keyboard": [[{"text": generalCopywriting.SEND_LOCATION_TEXT, "request_location": True}]]}
        elif currentQuestion['type'] == questionType.QUESTION_TYPE_BUILDING_ITEM:
            geolocation = temporaryAnswer['geolocation']
            # find nearby places
            nearbyPlaces = findNearestBuilding(geolocation['latitude'], geolocation['longitude'])
            # construct keyboard for reply
            buttonRows = [[buttonRow] for buttonRow in nearbyPlaces]
            buttonRows.append([{'text': 'Not in a building', 'value': None}])
            replyMarkup = buildInlineKeyboardMarkup(buttonRows, withNotSureOption=True)
        elif currentQuestion['type'] in questionType.SINGLE_VALIDATION_QUESTION_TYPES:
            keyboard = [[InlineKeyboardButton(generalCopywriting.VALIDATE_ANSWER_YES_TEXT, callback_data=callbackTypes.VALIDATION_ANSWER_TYPE_YES),
                        InlineKeyboardButton(generalCopywriting.VALIDATE_ANSWER_NO_TEXT, callback_data=callbackTypes.VALIDATION_ANSWER_TYPE_NO)],
                        [InlineKeyboardButton(generalCopywriting.VALIDATE_ANSWER_NOT_SURE_TEXT, callback_data=callbackTypes.VALIDATION_ANSWER_TYPE_NOT_SURE)]]


            replyMarkup = InlineKeyboardMarkup(keyboard)
        elif currentQuestion['type'] == questionType.QUESTION_TYPE_CATEGORIZATION:
            # load subcategory
            itemCategory = self.taskTemplate.itemCategory
            subcategories = Category.getSubcategories(itemCategory)
            # build inline button
            keyboardItems = []
            for subcategory in subcategories:
                keyboardItems.append([InlineKeyboardButton(subcategory['name'], callback_data=subcategory['_id'])])
            keyboardItems.append([InlineKeyboardButton(generalCopywriting.VALIDATE_ANSWER_NOT_SURE_TEXT, callback_data=callbackTypes.CATEGORIZATION_ANSWER_TYPE_NOT_SURE)])
            replyMarkup = InlineKeyboardMarkup(keyboardItems)
        elif currentQuestion['type'] == questionType.QUESTION_TYPE_WITH_CUSTOM_BUTTONS:
            replyMarkup = buildInlineKeyboardMarkup(currentQuestion['buttonRows'])
        else:
            replyMarkup = {"remove_keyboard": True}
        
        if currentQuestion['type'] == questionType.QUESTION_TYPE_SINGLE_VALIDATION_LOCATION:
            selectedItem = context.chat_data['selectedItem']
            bot.send_location(chat_id=chatId, latitude=selectedItem['location']['latitude'], longitude=selectedItem['location']['longitude'])
        bot.send_message(chat_id=chatId, text=formattedQuestion, reply_markup=replyMarkup, parse_mode='Markdown')

    def send_current_question_response(self, update, context):
        temporaryAnswer = context.chat_data['temporaryAnswer']
        currentQuestionNumber = context.chat_data['currentQuestionNumber']
        
        if update.callback_query:
            chatId = update.callback_query.message.chat_id
            context.bot.answer_callback_query(update.callback_query.id)
        else:
            chatId = update.message.chat_id
        currentQuestion = self.taskTemplate.questions[currentQuestionNumber]

        if 'responseOk' not in currentQuestion or currentQuestion['property'] not in temporaryAnswer:
            return
        
        if currentQuestion['type'] == questionType.QUESTION_TYPE_CATEGORIZATION:
            if temporaryAnswer[currentQuestion['property']] == callbackTypes.CATEGORIZATION_ANSWER_TYPE_NOT_SURE:
                formattedResponseOk = currentQuestion['responseNotSure']
            else:
                formattedResponseOk = currentQuestion['responseOk'].format(item=temporaryAnswer)
        else: 
            formattedResponseOk = currentQuestion['responseOk'].format(item=temporaryAnswer)

        replyMarkup = {"remove_keyboard": True}
        context.bot.send_message(chat_id=chatId, text=formattedResponseOk, reply_markup=replyMarkup, parse_mode='Markdown')

    def save_temporary_answer(self, update, context):
        temporaryAnswer = context.chat_data['temporaryAnswer']
        currentQuestionNumber = context.chat_data['currentQuestionNumber']
        currentQuestion = self.taskTemplate.questions[currentQuestionNumber]
        propertyName = currentQuestion['property']
        typeOfQuestion = currentQuestion['type']

        if typeOfQuestion == questionType.QUESTION_TYPE_TEXT:
            temporaryAnswer[propertyName] = update.message.text
        elif typeOfQuestion == questionType.QUESTION_TYPE_NUMBER:
            temporaryAnswer[propertyName] = int(update.message.text)
        elif typeOfQuestion == questionType.QUESTION_TYPE_IMAGE:
            # download image    
            fileName = update.message.photo[-1].file_id
            imageFile = update.message.photo[-1].get_file().download(custom_path='{imagePath}/{fileName}.jpg'.format(imagePath=env.IMAGE_DOWNLOAD_PATH, fileName=fileName))
            temporaryAnswer[propertyName] = u'{imageUrlPrefix}/{fileName}.jpg'.format(imageUrlPrefix=env.IMAGE_URL_PREFIX, fileName=fileName)
            temporaryAnswer['imageTelegramFileId'] = fileName
        elif typeOfQuestion == questionType.QUESTION_TYPE_LOCATION:
            temporaryAnswer[propertyName] = {'latitude': update.message.location.latitude, 'longitude': update.message.location.longitude}
        elif typeOfQuestion == questionType.QUESTION_TYPE_MULTIPLE_INPUT:
            splittedAnswers = [x.strip() for x in update.message.text.split(',')]
            temporaryAnswer[propertyName] = update.message.text
            temporaryAnswer[propertyName + '-list'] = splittedAnswers
        elif typeOfQuestion in questionType.SINGLE_VALIDATION_QUESTION_TYPES:
            temporaryAnswer[propertyName] = update.callback_query.data
        elif typeOfQuestion == questionType.QUESTION_TYPE_CATEGORIZATION:
            callbackData = update.callback_query.data
            if callbackData != callbackTypes.CATEGORIZATION_ANSWER_TYPE_NOT_SURE:
                subcategory = Category.getCategoryById(callbackData)
                temporaryAnswer[propertyName] = subcategory     
        elif typeOfQuestion == questionType.QUESTION_TYPE_WITH_CUSTOM_BUTTONS:
            callbackData = json.loads(update.callback_query.data)
            temporaryAnswer[propertyName] = callbackData['value']
        elif typeOfQuestion == questionType.QUESTION_TYPE_BUILDING_ITEM:
            if update.message:
                temporaryAnswer[propertyName] = update.message.text
            else:
                callbackData = json.loads(update.callback_query.data)
                if callbackData['value'] is None:
                    temporaryAnswer[propertyName] = None
                elif callbackData['value'] != callbackTypes.GENERAL_ANSWER_TYPE_NOT_SURE:
                    item = Item.getItemById(callbackData['value'], 'placeItems')
                    temporaryAnswer[propertyName] = item     

        pprint(temporaryAnswer)
    
    def send_closing_statement(self, update, context):
        temporaryAnswer = context.chat_data['temporaryAnswer']

        if update.callback_query:
            chatId = update.callback_query.message.chat_id
        else:
            chatId = update.message.chat_id

        formattedClosingStatement = self.taskTemplate.closingStatement.format(item=temporaryAnswer)

        replyMarkup = {"remove_keyboard": True}
        context.bot.send_message(chat_id=chatId, text=formattedClosingStatement, reply_markup=replyMarkup, parse_mode='Markdown')

    def save_answers(self, temporaryAnswer, user):
        '''
        userId = user['_id']
        if self.taskTemplate.type == taskType.TASK_TYPE_CREATE_ITEM: # task type 
            data = temporaryAnswer
            data['itemType'] = self.taskTemplate.itemType
            data['authorId'] = userId
            FirestoreClient.saveDocument('items', data=data)
        elif self.taskTemplate.type == taskType.TASK_TYPE_VALIDATE_ITEM:
            validations = []
            selectedItem = chat_data['selectedItem']
            for question in self.taskTemplate.questions:
                validations.append({
                    'propertyName': question['property'],
                    'propertyValue': selectedItem[question['property']],
                    'validation': temporaryAnswer[question['property']],
                    'userId': userId
                })
            FirestoreClient.updateArrayInDocument('items', selectedItem['_id'], 'validations', validations)
        elif self.taskTemplate.type == taskType.TASK_TYPE_CATEGORIZE_ITEM:
            categorizations = []
            selectedItem = chat_data['selectedItem']
            answers = []
            for itemType in temporaryAnswer['itemType']:
                if itemType != callbackTypes.CATEGORIZATION_ANSWER_TYPE_NOT_SURE:
                    answers.append(itemType['_ref'])
                else:
                    answers.append(None)
            categorizations.append({
                'propertyName': u'itemType',
                'propertyValue': answers,
                'userId': userId})
            FirestoreClient.updateArrayInDocument('items', selectedItem['_id'], 'categorizations', categorizations)
        elif self.taskTemplate.type == taskType.TASK_TYPE_ENRICH_ITEM:
            enrichments = []
            selectedItem = chat_data['selectedItem']
            answers = []
            for question in self.taskTemplate.questions:
                enrichments.append({
                    'propertyName': question['property'],
                    'propertyValue': temporaryAnswer[question['property']],
                    'userId': userId
                })
            FirestoreClient.updateArrayInDocument('items', selectedItem['_id'], 'enrichments', enrichments)
        '''
            
    # callbacks
    def _start_task_callback(self, update, context):
        bot = context.bot
        context.chat_data['userId'] = update.message.from_user.id
        context.chat_data['temporaryAnswer'] = {
            'executionStartTime': datetime.now(tzlocal())
        }
        context.chat_data['chatId'] = update.message.chat_id
        context.chat_data['currentQuestionNumber'] = 0
        # to-do: update context task instance

        bot.send_message(chat_id=update.message.chat_id, text=self.taskTemplate.openingStatement, parse_mode='Markdown')
        
        self.send_current_question(update, context)
        return context.chat_data['currentQuestionNumber']
        
    # individual state callback
    def _question_callback(self, update, context):
        # save to temporary answer
        self.save_temporary_answer(update, context)
        # send response of current question
        self.send_current_question_response(update, context)

        # update question number in context
        currentQuestionNumber = context.chat_data['currentQuestionNumber']

        # check jump rule
        currentQuestion = self.taskTemplate.questions[currentQuestionNumber]
        shouldJump = False
        if 'jumpRules' in currentQuestion:
            shouldJump, jumpIndex = logicJumpHelper.evaluateJumpRules(context.chat_data['temporaryAnswer'], currentQuestion['jumpRules'])
        
        if shouldJump:
            currentQuestionNumber = jumpIndex
        else:
            currentQuestionNumber += 1
        context.chat_data['currentQuestionNumber'] = currentQuestionNumber

        if currentQuestionNumber >= self.numOfStates or currentQuestionNumber == ConversationHandler.END:
            currentQuestionNumber = ConversationHandler.END
            self.save_answers(context.chat_data['temporaryAnswer'], context.chat_data['user'])
            self.send_closing_statement(update, context)
        else:
            self.send_current_question(update, context)

        return currentQuestionNumber

    # fallback
    def _fallbackCallback(self, update, context):
        currentQuestionNumber = context.chat_data['currentQuestionNumber']
        temporaryAnswer = context.chat_data['temporaryAnswer']
        currentQuestion = self.taskTemplate.questions[currentQuestionNumber]
        formattedResponseError = currentQuestion['responseError'].format(item=temporaryAnswer)
        context.bot.send_message(chat_id=update.message.chat_id, text=formattedResponseError, parse_mode='Markdown')

        return currentQuestionNumber