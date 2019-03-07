from db.task import Task
from db.item import Item
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from dialoguemanager.response import generalCopywriting
import db.firestoreClient as FirestoreClient
from common.placeUtility import findNearestPlaceItem
from common.constants import taskType
from common.constants import questionType
from client.telegramClient import dispatcher
from pprint import pprint

class TaskExecutioner(object):
    '''Execute a certain task

    Attributes:
        task: the task data loaded from database
        currentQuestionNumber: the current state (question number) of executing the task
    '''

    def __init__(self, taskId):
        self.task = Task.getTaskById(taskId) # load task from db
        self.initConversationHandler()
        if self.task.type == taskType.TASK_TYPE_VALIDATE_ITEM:
            self.initQuestionData()

    def initConversationHandler(self):
        # entry points
        entryPoints = [CommandHandler(self.task.entryCommand, self._startTaskCallback)]
        # create states
        states = {}
        hasConfirmation = False

        for questionNumber, question in enumerate(self.task.questions):
            # create handler
            if question['type'] == questionType.QUESTION_TYPE_IMAGE:
                handler = MessageHandler(Filters.photo, self._questionCallback)
            elif question['type'] == questionType.QUESTION_TYPE_LOCATION:
                handler = MessageHandler(Filters.location, self._questionCallback)
            elif question['type'] in questionType.TEXT_BASED_QUESTION_TYPES:
                handler = MessageHandler(Filters.text, self._questionCallback)
            elif question['type'] in questionType.SINGLE_VALIDATION_QUESTION_TYPES:
                handler = CallbackQueryHandler(self._questionCallback)
            states[questionNumber] = [handler]
            
            if 'confirmationText' in question: 
                hasConfirmation = True

        if hasConfirmation:
            states[len(self.task.questions)] = [MessageHandler(Filters.text, self._confirmationCallback)]
            self.numOfStates = len(self.task.questions) + 1
        else:
            self.numOfStates = len(self.task.questions)

        self.conversationHandler = ConversationHandler(entry_points=entryPoints, states=states, fallbacks=[MessageHandler(Filters.all, self._fallbackCallback)])

    def initQuestionData(self):
        # load items with corresponding itemType
        self.questionData = Item.getItemsByType(self.task.itemType)[-1] # TO-DO assign item here

    def sendCurrentQuestion(self, update, context):
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

        currentQuestion = self.task.questions[currentQuestionNumber]
        if self.task.type == taskType.TASK_TYPE_CREATE_ITEM:
            formattedQuestion = currentQuestion['text'].format(item=temporaryAnswer)
        else:
            formattedQuestion = currentQuestion['text'].format(item=self.questionData)

        if currentQuestion['type'] == questionType.QUESTION_TYPE_LOCATION:
            replyMarkup = {"keyboard": [[{"text": generalCopywriting.SEND_LOCATION_TEXT, "request_location": True}]]}
        elif currentQuestion['type'] == questionType.QUESTION_TYPE_LOCATION_NAME:
            locationAnswer = temporaryAnswer['location']
            # find nearby places
            nearbyPlaces = findNearestPlaceItem(locationAnswer['latitude'], locationAnswer['longitude'])
            print(nearbyPlaces)
            # construct keyboard for reply
            keyboardReply = []
            for place in nearbyPlaces:
                keyboardReply.append([place['name']])
            replyMarkup = {"keyboard": keyboardReply}
        elif currentQuestion['type'] in questionType.SINGLE_VALIDATION_QUESTION_TYPES:
            keyboard = [[InlineKeyboardButton(generalCopywriting.VALIDATE_ANSWER_YES_TEXT, callback_data='0'),
                        InlineKeyboardButton(generalCopywriting.VALIDATE_ANSWER_NO_TEXT, callback_data='1')],
                        [InlineKeyboardButton(generalCopywriting.VALIDATE_ANSWER_NOT_SURE_TEXT, callback_data='2')]]
            replyMarkup = InlineKeyboardMarkup(keyboard)
        else:
            replyMarkup = {"remove_keyboard": True}
        
        if currentQuestion['type'] == questionType.QUESTION_TYPE_SINGLE_VALIDATION_LOCATION:
            bot.send_location(chat_id=chatId, latitude=self.questionData['location']['latitude'], longitude=self.questionData['location']['longitude'])
        bot.send_message(chat_id=chatId, text=formattedQuestion, reply_markup=replyMarkup, parse_mode='Markdown')

    def sendCurrentQuestionResponse(self, update, context):
        temporaryAnswer = context.chat_data['temporaryAnswer']
        currentQuestionNumber = context.chat_data['currentQuestionNumber']

        if update.callback_query:
            chatId = update.callback_query.message.chat_id
        else:
            chatId = update.message.chat_id
        currentQuestion = self.task.questions[currentQuestionNumber]
        formattedResponseOk = currentQuestion['responseOk'].format(item=temporaryAnswer)
        replyMarkup = {"remove_keyboard": True}
        context.bot.send_message(chat_id=chatId, text=formattedResponseOk, reply_markup=replyMarkup, parse_mode='Markdown')

    def saveTemporaryAnswer(self, update, context):
        temporaryAnswer = context.chat_data['temporaryAnswer']
        currentQuestionNumber = context.chat_data['currentQuestionNumber']

        currentQuestion = self.task.questions[currentQuestionNumber]
        propertyName = currentQuestion['property']
        if currentQuestion['type'] in [questionType.QUESTION_TYPE_TEXT, questionType.QUESTION_TYPE_LOCATION_NAME]:
            temporaryAnswer[propertyName] = update.message.text
        elif currentQuestion['type'] == questionType.QUESTION_TYPE_IMAGE:
            temporaryAnswer[propertyName] = update.message.photo[0].file_id
        elif currentQuestion['type'] == questionType.QUESTION_TYPE_LOCATION:
            temporaryAnswer[propertyName] = {'latitude': update.message.location.latitude, 'longitude': update.message.location.longitude}
        elif currentQuestion['type'] == questionType.QUESTION_TYPE_MULTIPLE_INPUT:
            splittedAnswers = [x.strip() for x in update.message.text.split(',')]
            temporaryAnswer[propertyName] = update.message.text
            temporaryAnswer[propertyName + '-list'] = splittedAnswers
        elif currentQuestion['type'] in questionType.SINGLE_VALIDATION_QUESTION_TYPES:
            temporaryAnswer[propertyName] = update.callback_query.data
        
    def sendConfirmation(self, update, context):
        bot = context.bot
        temporaryAnswer = context.chat_data['temporaryAnswer']
        if update.callback_query:
            chatId = update.callback_query.message.chat_id
        else:
            chatId = update.message.chat_id

        for question in self.task.questions:
            if 'confirmationText' in question:
                formattedConfirmation = question['confirmationText'].format(item=temporaryAnswer)
                if question['type'] in questionType.TEXT_BASED_QUESTION_TYPES:
                    bot.send_message(chat_id=chatId, text=formattedConfirmation, parse_mode='Markdown')
                elif question['type'] == questionType.QUESTION_TYPE_IMAGE:
                    image = temporaryAnswer[question['property']]
                    bot.send_photo(chat_id=chatId, photo=image, caption=formattedConfirmation, parse_mode='Markdown')
                elif question['type'] == questionType.QUESTION_TYPE_LOCATION:
                    location = temporaryAnswer[question['property']]
                    bot.send_message(chat_id=chatId, text=formattedConfirmation, parse_mode='Markdown')
                    bot.send_location(chat_id=chatId, latitude=location['latitude'], longitude=location['longitude'])

        # send is that correct
        replyMarkup = {"keyboard": [[generalCopywriting.YES_BUTTON_TEXT], [generalCopywriting.NO_BUTTON_TEXT]]}
        bot.send_message(chat_id=chatId, text=generalCopywriting.ASK_DATA_CONFIRMATION_TEXT, reply_markup=replyMarkup, parse_mode='Markdown')


    def sendClosingStatement(self, update, context):
        temporaryAnswer = context.chat_data['temporaryAnswer']
        if update.callback_query:
            chatId = update.callback_query.message.chat_id
        else:
            chatId = update.message.chat_id

        if self.task.type == taskType.TASK_TYPE_CREATE_ITEM:
            formattedClosingStatement = self.task.closingStatement.format(item=temporaryAnswer)
        else:
            formattedClosingStatement = self.task.closingStatement.format(item=self.questionData)

        replyMarkup = {"remove_keyboard": True}
        context.bot.send_message(chat_id=chatId, text=formattedClosingStatement, reply_markup=replyMarkup, parse_mode='Markdown')

    def saveAnswers(self, chat_data):
        temporaryAnswer = chat_data['temporaryAnswer']
        if self.task.type == taskType.TASK_TYPE_CREATE_ITEM: # task type 
            data = temporaryAnswer
            data['itemType'] = self.task.itemType
            data['authorId'] = chat_data['userId']
            FirestoreClient.saveDocument('items', data=data)
        elif self.task.type == taskType.TASK_TYPE_VALIDATE_ITEM:
            validations = []
            for question in self.task.questions:
                validations.append({
                    'propertyName': question['property'],
                    'propertyValue': self.questionData[question['property']],
                    'validation': temporaryAnswer[question['property']],
                    'userId': chat_data['userId']
                })
            FirestoreClient.updateArrayInDocument('items', self.questionData['_id'], 'validations', validations)
            
    # callbacks
    def _startTaskCallback(self, update, context):
        bot = context.bot
        context.chat_data['userId'] = update.message.from_user.id
        context.chat_data['temporaryAnswer'] = {}
        context.chat_data['chatId'] = update.message.chat_id
        context.chat_data['currentQuestionNumber'] = 0

        bot.send_message(chat_id=update.message.chat_id, text=self.task.openingStatement, parse_mode='Markdown')
        if self.task.type == taskType.TASK_TYPE_VALIDATE_ITEM and 'image' in self.questionData:
            bot.send_photo(chat_id=update.message.chat_id, photo=self.questionData['image'], parse_mode='Markdown')
        self.sendCurrentQuestion(update, context)

        return context.chat_data['currentQuestionNumber']

    # individual state callback
    def _questionCallback(self, update, context):
        # save to temporary answer
        self.saveTemporaryAnswer(update, context)
        # send response of current question
        self.sendCurrentQuestionResponse(update, context)

        # update question number in context
        currentQuestionNumber = context.chat_data['currentQuestionNumber']
        # move to next question
        currentQuestionNumber += 1
        context.chat_data['currentQuestionNumber'] = currentQuestionNumber
        if currentQuestionNumber >= self.numOfStates:
            currentQuestionNumber = ConversationHandler.END
            self.saveAnswers(context.chat_data)
            self.sendClosingStatement(update, context)
        elif currentQuestionNumber >= len(self.task.questions):
            self.sendConfirmation(update, context)
        else:
            self.sendCurrentQuestion(update, context)

        return currentQuestionNumber

    def _confirmationCallback(self, update, context):
        self.saveAnswers(context.chat_data)
        self.sendClosingStatement(update, context)

        return ConversationHandler.END

    # fallback
    def _fallbackCallback(self, update, context):
        currentQuestionNumber = context.chat_data['currentQuestionNumber']

        temporaryAnswer = context.chat_data['temporaryAnswer']
        currentQuestion = self.task.questions[currentQuestionNumber]
        formattedResponseError = currentQuestion['responseError'].format(item=temporaryAnswer)
        context.bot.send_message(chat_id=update.message.chat_id, text=formattedResponseError, parse_mode='Markdown')

        return currentQuestionNumber