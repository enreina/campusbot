from db.taskTemplate import TaskTemplate
from db.user import User
from db.item import Item
from db.course import Course
from db.category import Category
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from dialoguemanager.response import generalCopywriting
import db.firestoreClient as FirestoreClient
from common.placeUtility import findNearestPlace
from common.constants import taskType, questionType, specialStates, callbackTypes
from pprint import pprint
from common.inlineKeyboardHelper import buildInlineKeyboardMarkup
from common import logicJumpHelper
import re
import settings as env
import json

class GenericFlowHandler(object):
    '''Abstraction of a task flow handler

    Attributes:
        taskTemplate: the task tempalate data loaded from database
        dispatcher: the dispatcher used by telegram bot api
    '''

    def __init__(self, taskTemplateId, dispatcher, itemCollectionName='items', entryCommand=None):
        self.taskTemplate = TaskTemplate.getTaskTemplateById(taskTemplateId) # load task from db
        self.dispatcher = dispatcher
        self.itemCollectionName = itemCollectionName
        if entryCommand is None:
            self.entryCommand = self.taskTemplate.entryCommand
        else:
            self.entryCommand = entryCommand

    def init_conversation_handler(self, user):
        # entry points
        entryPoints = [CommandHandler(self.entryCommand, self._start_task_callback, filters=Filters.user(int(user['telegramId'])))]
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
                if 'regexRule' in question:
                    regexRule = r'{regexRule}'.format(regexRule=question['regexRule'])
                else:
                    regexRule = r'^\s*[0-9]*.?[0-9]+\s*$'
                handler.append(MessageHandler(Filters.regex(regexRule), self._question_callback))
            elif question['type'] in questionType.TEXT_BASED_QUESTION_TYPES:
                handler.append(MessageHandler(Filters.text, self._question_callback))
            elif question['type'] in questionType.INLINE_BUTTON_BASED_QUESTION_TYPES:
                handler.append(CallbackQueryHandler(self._question_callback))
            
            if question['type'] == questionType.QUESTION_TYPE_MULTIPLE_CHOICE_ITEM:
                handler.append(MessageHandler(Filters.text, self._question_callback))

            isRequired = 'isRequired' in question and question['isRequired']
            if not isRequired:
                handler.append(CommandHandler('skip', self._skip_question_callback))
            
            states[questionNumber] = handler
        self.numOfStates = len(self.taskTemplate.questions)
        conversationName = '{telegramId}-{entryCommand}'.format(telegramId=user['telegramId'], entryCommand=self.entryCommand)
        self.conversationHandler = ConversationHandler(entry_points=entryPoints, states=states, fallbacks=[MessageHandler(Filters.all, self._fallbackCallback)], persistent=True, name=conversationName)

    def add_to_dispatcher(self, user):
        self.init_conversation_handler(user)
        self.dispatcher.add_handler(self.conversationHandler)

    def remove_from_dispatcher(self):
        self.dispatcher.remove_handler(self.conversationHandler)
    
    def send_current_question(self, update, context):
        bot = context.bot
        if 'temporaryAnswer' in context.chat_data:
            temporaryAnswer = context.chat_data['temporaryAnswer']
        else:
            temporaryAnswer = {}
        
        if 'currentQuestionNumber' in context.chat_data:
            currentQuestionNumber = context.chat_data['currentQuestionNumber']
        else:
            currentQuestionNumber = 0

        if update.callback_query:
            chatId = update.callback_query.message.chat_id
        else:
            chatId = update.message.chat_id

        currentQuestion = self.taskTemplate.questions[currentQuestionNumber]

        if currentQuestion['type'] == questionType.QUESTION_TYPE_LOCATION:
            replyMarkup = {"keyboard": [[{"text": generalCopywriting.SEND_LOCATION_TEXT, "request_location": True}]]}
        elif currentQuestion['type'] == questionType.QUESTION_TYPE_MULTIPLE_CHOICE_ITEM:
            if 'geolocation' in temporaryAnswer:
                geolocation = temporaryAnswer['geolocation']
            else:
                geolocation = {'latitude': 0, 'longitude': 0}
            # find nearby places
            nearbyPlaces = findNearestPlace(geolocation['latitude'], geolocation['longitude'], itemCategory=currentQuestion['choiceItemCategory'])
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
        elif currentQuestion['type'] == questionType.QUESTION_TYPE_CHECK_COURSE:
            temporaryAnswer['doesCourseExist'] = False
            course = Course.find_course_by_name(temporaryAnswer['courseName'])
            # if course does not exist, move to next question
            if course is None:
                return self.move_to_next_question(update, context)
            temporaryAnswer['course'] = course
            replyMarkup = buildInlineKeyboardMarkup(currentQuestion['buttonRows'])
        else:
            replyMarkup = {"remove_keyboard": True}

        # check must have properties
        if 'mustHaveProperties' in currentQuestion:
            for prop in currentQuestion['mustHaveProperties']:
                if prop not in temporaryAnswer or temporaryAnswer[prop] is None:
                    return self.move_to_next_question(update, context)

        if 'multiItemPropertyName' in currentQuestion:
            # handle question with multiple input
            if 'currentItemIndex' not in context.chat_data:
                context.chat_data['currentItemIndex'] = 0
            currentItemIndex = context.chat_data['currentItemIndex']
            item = temporaryAnswer[currentQuestion['multiItemPropertyName']][currentItemIndex]
            formattedQuestion = currentQuestion['text'].format(item=item, idx=currentItemIndex+1)
        else:
            formattedQuestion = currentQuestion['text'].format(item=temporaryAnswer)

        message = bot.send_message(chat_id=chatId, text=formattedQuestion, reply_markup=replyMarkup, parse_mode='Markdown')
        User.saveUtterance(context.chat_data['userId'], message, byBot=True)

        return currentQuestionNumber

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
        message = context.bot.send_message(chat_id=chatId, text=formattedResponseOk, reply_markup=replyMarkup, parse_mode='Markdown')
        User.saveUtterance(context.chat_data['userId'], message, byBot=True)

    def save_temporary_answer(self, update, context):
        temporaryAnswer = context.chat_data['temporaryAnswer']
        currentQuestionNumber = context.chat_data['currentQuestionNumber']
        currentQuestion = self.taskTemplate.questions[currentQuestionNumber]
        propertyName = currentQuestion['property']
        typeOfQuestion = currentQuestion['type']
        answer = None

        if typeOfQuestion == questionType.QUESTION_TYPE_TEXT:
            answer = update.message.text
        elif typeOfQuestion == questionType.QUESTION_TYPE_NUMBER:
            try:
                answer = int(update.message.text)
            except:
                answer = float(update.message.text)
        elif typeOfQuestion == questionType.QUESTION_TYPE_IMAGE:
            # download image    
            fileName = update.message.photo[-1].file_id
            imageFile = update.message.photo[-1].get_file().download(custom_path='{imagePath}/{fileName}.jpg'.format(imagePath=env.IMAGE_DOWNLOAD_PATH, fileName=fileName))
            answer = u'{imageUrlPrefix}/{fileName}.jpg'.format(imageUrlPrefix=env.IMAGE_URL_PREFIX, fileName=fileName)
            temporaryAnswer['imageTelegramFileId'] = fileName
        elif typeOfQuestion == questionType.QUESTION_TYPE_LOCATION:
            answer = {'latitude': update.message.location.latitude, 'longitude': update.message.location.longitude}
        elif typeOfQuestion == questionType.QUESTION_TYPE_MULTIPLE_INPUT:
            splittedAnswers = [x.strip() for x in update.message.text.split(',')]
            answer = splittedAnswers
            if 'propertyToConcat' in currentQuestion:
                temporaryAnswer[currentQuestion['propertyToConcat']] = update.message.text
        elif typeOfQuestion in questionType.SINGLE_VALIDATION_QUESTION_TYPES:
            answer = update.callback_query.data
        elif typeOfQuestion == questionType.QUESTION_TYPE_CATEGORIZATION:
            callbackData = update.callback_query.data
            if callbackData != callbackTypes.CATEGORIZATION_ANSWER_TYPE_NOT_SURE:
                subcategory = Category.getCategoryById(callbackData)
                answer = subcategory     
                temporaryAnswer['categoryName'] = subcategory['name']
        elif typeOfQuestion in [questionType.QUESTION_TYPE_WITH_CUSTOM_BUTTONS, questionType.QUESTION_TYPE_CHECK_COURSE]:
            callbackData = json.loads(update.callback_query.data)
            answer = callbackData['value']
        elif typeOfQuestion == questionType.QUESTION_TYPE_MULTIPLE_CHOICE_ITEM:
            if update.message:
                answer = update.message.text
            else:
                callbackData = json.loads(update.callback_query.data)
                if callbackData['value'] is None:
                    answer = None
                elif callbackData['value'] != callbackTypes.GENERAL_ANSWER_TYPE_NOT_SURE:
                    item = Item.getItemById(callbackData['value'], 'placeItems')
                    answer = item     

        if 'multiItemPropertyName' in currentQuestion:
            # handle question with multiple input
            currentItemIndex = context.chat_data['currentItemIndex']
            item = temporaryAnswer[currentQuestion['multiItemPropertyName']][currentItemIndex]
            saveAsArray = 'saveAsArray' in currentQuestion and currentQuestion['saveAsArray']
            if not saveAsArray:
                answer = {'propertyName': unicode(item), 'propertyValue': answer}
            else:
                if answer is not None and answer:
                    answer = item
            if propertyName in temporaryAnswer:
                if saveAsArray and answer or not saveAsArray:
                    temporaryAnswer[propertyName].append(answer)
            else:
                if saveAsArray and answer or not saveAsArray:
                    temporaryAnswer[propertyName] = [answer]
        else:
            temporaryAnswer[propertyName] = answer
        
        pprint(temporaryAnswer)
    
    def send_closing_statements(self, update, context):
        temporaryAnswer = context.chat_data['temporaryAnswer']

        if update.callback_query:
            chatId = update.callback_query.message.chat_id
        else:
            chatId = update.message.chat_id

        for statement in self.taskTemplate.closingStatements:
            formattedClosingStatement = statement.format(item=temporaryAnswer)

            replyMarkup = {"remove_keyboard": True}
            message = context.bot.send_message(chat_id=chatId, text=formattedClosingStatement, reply_markup=replyMarkup, parse_mode='Markdown')
            User.saveUtterance(context.chat_data['userId'], message, byBot=True)

    def save_answers(self, update, context):
        return
            
    # callbacks
    def _start_task_callback(self, update, context):
        bot = context.bot
        context.chat_data['userId'] = update.message.from_user.id
        context.chat_data['chatId'] = update.message.chat_id
        context.chat_data['currentQuestionNumber'] = 0
        User.saveUtterance(update.message.from_user.id, update.message)

        for statement in self.taskTemplate.openingStatements:
            item = None
            if 'temporaryAnswer' in context.chat_data:
                item = context.chat_data['temporaryAnswer']
            
            if isinstance(statement, dict):
                if 'imagePropertyName' in statement:
                    image = item[statement['imagePropertyName']]
                    caption=None
                    if 'imageCaption' in statement:
                        caption = statement['imageCaption'].format(item=item)

                    message = bot.send_photo(chat_id=update.message.chat_id, photo=image, caption=caption, parse_mode='Markdown')
                    User.saveUtterance(context.chat_data['userId'], message, byBot=True)
                if 'jumpRules' in statement:
                    jumpRules = statement['jumpRules']
                    shouldJump, jumpIndex = logicJumpHelper.evaluateJumpRules(item, jumpRules)

                    if shouldJump:
                        context.chat_data['currentQuestionNumber'] = jumpIndex
            else:
                message = bot.send_message(chat_id=update.message.chat_id, text=statement.format(item=item), parse_mode='Markdown')
                User.saveUtterance(context.chat_data['userId'], message, byBot=True)

        self.send_current_question(update, context)
        return context.chat_data['currentQuestionNumber']
        
    # individual state callback
    def _question_callback(self, update, context):
        if update.message:
            message = update.message
        else:
            message = update.callback_query.message
        User.saveUtterance(context.chat_data['userId'], message, callbackQuery=update.callback_query)
        # save to temporary answer
        self.save_temporary_answer(update, context)
        # send response of current question
        self.send_current_question_response(update, context)

        return self.move_to_next_question(update, context)

    # callback for skipping question
    def _skip_question_callback(self, update, context):
        User.saveUtterance(update.message.from_user.id, update.message)
        # remove any answer from temp answer
        temporaryAnswer = context.chat_data['temporaryAnswer']
        currentQuestionNumber = context.chat_data['currentQuestionNumber']
        currentQuestion = self.taskTemplate.questions[currentQuestionNumber]
        propertyName = currentQuestion['property']
        if 'multiItemPropertyName' in currentQuestion:
            # handle question with multiple input
            currentItemIndex = context.chat_data['currentItemIndex']
            item = temporaryAnswer[currentQuestion['multiItemPropertyName']][currentItemIndex]
            answer = {'propertyName': unicode(item), 'propertyValue': None}
            saveAsArray = 'saveAsArray' in currentQuestion and currentQuestion['saveAsArray']
            if not saveAsArray:
                if propertyName in temporaryAnswer:
                    temporaryAnswer[propertyName].append(answer)
                else:
                    temporaryAnswer[propertyName] = [answer]
        elif propertyName in temporaryAnswer:
            del temporaryAnswer[propertyName]

        return self.move_to_next_question(update, context)

    def move_to_next_question(self, update, context):
        # update question number in context
        currentQuestionNumber = context.chat_data['currentQuestionNumber']
        currentQuestion = self.taskTemplate.questions[currentQuestionNumber]
        
        # retain current question if still in multiple item question
        if 'multiItemPropertyName' in currentQuestion:
            # add 1 to index of multiple item index
            currentItemIndex = context.chat_data['currentItemIndex']
            currentItemIndex = currentItemIndex + 1
            temporaryAnswer = context.chat_data['temporaryAnswer']

            if currentItemIndex >= len(temporaryAnswer[currentQuestion['multiItemPropertyName']]):
                del context.chat_data['currentItemIndex']
            else:
                context.chat_data['currentItemIndex'] = currentItemIndex
                return self.send_current_question(update, context)


        # check jump rule
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
            self.save_answers(update, context)
            self.send_closing_statements(update, context)

            if 'currentTaskInstance' in context.chat_data:
                del context.chat_data['currentTaskInstance']
            self.remove_from_dispatcher()
        else:
            return self.send_current_question(update, context)

        return currentQuestionNumber

    # fallback
    def _fallbackCallback(self, update, context):
        User.saveUtterance(context.chat_data['userId'], update.message)

        currentQuestionNumber = context.chat_data['currentQuestionNumber']
        temporaryAnswer = context.chat_data['temporaryAnswer']
        currentQuestion = self.taskTemplate.questions[currentQuestionNumber]
        formattedResponseError = currentQuestion['responseError'].format(item=temporaryAnswer)
        message = context.bot.send_message(chat_id=update.message.chat_id, text=formattedResponseError, parse_mode='Markdown')
        User.saveUtterance(update.message.chat_id, message, byBot=True)

        return currentQuestionNumber