from db.task import Task
from db.item import Item
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from dialoguemanager.response import generalCopywriting
import db.firestoreClient as FirestoreClient
from common.placeUtility import findNearestPlaceItem
from common.constants import taskType
from common.constants import questionType

class TaskExecutioner(object):
    '''Execute a certain task

    Attributes:
        task: the task data loaded from database
        currentQuestionNumber: the current state (question number) of executing the task
    '''

    def __init__(self, taskId):
        self.task = Task.getTaskById(taskId) # load task from db
        self.currentQuestionNumber = 0 # start from opening statement
        self.temporaryAnswer = {}
        self.initConversationHandler()
        if self.task.type == taskType.TASK_TYPE_VALIDATE_ITEM:
            self.initQuestionData()

    def initConversationHandler(self):
        # entry points
        def startTask(bot, update):
            self.currentQuestionNumber = 0

            bot.send_message(chat_id=update.message.chat_id, text=self.task.openingStatement, parse_mode='Markdown')
            if self.task.type == taskType.TASK_TYPE_VALIDATE_ITEM and 'image' in self.questionData:
                bot.send_photo(chat_id=update.message.chat_id, photo=self.questionData['image'], parse_mode='Markdown')
            self.sendCurrentQuestion(bot, update)

            return self.currentQuestionNumber

        entryPoints = [CommandHandler(self.task.entryCommand, startTask)]

        # individual state handler
        def questionHandler(bot, update):
            # save to temporary answer
            self.saveTemporaryAnswer(bot, update)
            # send response of current question
            self.sendCurrentQuestionResponse(bot, update)

            # move to next question
            self.currentQuestionNumber += 1
            if self.currentQuestionNumber >= self.numOfStates:
                self.currentQuestionNumber = ConversationHandler.END
                self.saveAnswers()
                self.sendClosingStatement(bot, update)
            elif self.currentQuestionNumber >= len(self.task.questions):
                self.sendConfirmation(bot, update)
            else:
                self.sendCurrentQuestion(bot, update)

            return self.currentQuestionNumber

        def confirmationHandler(bot, update):
            self.saveAnswers()
            self.sendClosingStatement(bot, update)

            return ConversationHandler.END

        states = {}
        hasConfirmation = False

        for questionNumber, question in enumerate(self.task.questions):
            # create handler
            if question['type'] == questionType.QUESTION_TYPE_IMAGE:
                handler = MessageHandler(Filters.photo, questionHandler)
            elif question['type'] == questionType.QUESTION_TYPE_LOCATION:
                handler = MessageHandler(Filters.location, questionHandler)
            elif question['type'] in questionType.TEXT_BASED_QUESTION_TYPES:
                handler = MessageHandler(Filters.text, questionHandler)
            elif question['type'] in questionType.SINGLE_VALIDATION_QUESTION_TYPES:
                handler = CallbackQueryHandler(questionHandler)
            states[questionNumber] = [handler]
            
            if 'confirmationText' in question: 
                hasConfirmation = True

        if hasConfirmation:
            states[len(self.task.questions)] = [MessageHandler(Filters.text, confirmationHandler)]
            self.numOfStates = len(self.task.questions) + 1
        else:
            self.numOfStates = len(self.task.questions)
        

        # fallback
        def fallback(bot, update):
            currentQuestion = self.task.questions[self.currentQuestionNumber]
            formattedResponseError = currentQuestion['responseError'].format(item=self.temporaryAnswer)
            bot.send_message(chat_id=update.message.chat_id, text=formattedResponseError, parse_mode='Markdown')

            return self.currentQuestionNumber

        self.conversationHandler = ConversationHandler(entry_points=entryPoints, states=states, fallbacks=[MessageHandler(Filters.all, fallback)])

    def initQuestionData(self):
        # load items with corresponding itemType
        self.questionData = Item.getItemsByType(self.task.itemType)[0] # TO-DO assign item here

    def sendCurrentQuestion(self, bot, update):
        if update.callback_query:
            chatId = update.callback_query.message.chat_id
        else:
            chatId = update.message.chat_id

        currentQuestion = self.task.questions[self.currentQuestionNumber]
        if self.task.type == taskType.TASK_TYPE_CREATE_ITEM:
            formattedQuestion = currentQuestion['text'].format(item=self.temporaryAnswer)
        else:
            formattedQuestion = currentQuestion['text'].format(item=self.questionData)

        if currentQuestion['type'] == questionType.QUESTION_TYPE_LOCATION:
            replyMarkup = {"keyboard": [[{"text": generalCopywriting.SEND_LOCATION_TEXT, "request_location": True}]]}
        elif currentQuestion['type'] == questionType.QUESTION_TYPE_LOCATION_NAME:
            locationAnswer = self.temporaryAnswer['location']
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

    def sendCurrentQuestionResponse(self, bot, update):
        if update.callback_query:
            chatId = update.callback_query.message.chat_id
        else:
            chatId = update.message.chat_id
        currentQuestion = self.task.questions[self.currentQuestionNumber]
        formattedResponseOk = currentQuestion['responseOk'].format(item=self.temporaryAnswer)
        replyMarkup = {"remove_keyboard": True}
        bot.send_message(chat_id=chatId, text=formattedResponseOk, reply_markup=replyMarkup, parse_mode='Markdown')

    def saveTemporaryAnswer(self, bot, update):
        currentQuestion = self.task.questions[self.currentQuestionNumber]
        propertyName = currentQuestion['property']
        if currentQuestion['type'] in [questionType.QUESTION_TYPE_TEXT, questionType.QUESTION_TYPE_LOCATION_NAME]:
            self.temporaryAnswer[propertyName] = update.message.text
        elif currentQuestion['type'] == questionType.QUESTION_TYPE_IMAGE:
            self.temporaryAnswer[propertyName] = update.message.photo[0].file_id
        elif currentQuestion['type'] == questionType.QUESTION_TYPE_LOCATION:
            self.temporaryAnswer[propertyName] = {'latitude': update.message.location.latitude, 'longitude': update.message.location.longitude}
        elif currentQuestion['type'] == questionType.QUESTION_TYPE_MULTIPLE_INPUT:
            splittedAnswers = [x.strip() for x in update.message.text.split(',')]
            self.temporaryAnswer[propertyName] = update.message.text
            self.temporaryAnswer[propertyName + '-list'] = splittedAnswers
        elif currentQuestion['type'] in questionType.SINGLE_VALIDATION_QUESTION_TYPES:
            self.temporaryAnswer[propertyName] = update.callback_query.data
        
    def sendConfirmation(self, bot, update):
        if update.callback_query:
            chatId = update.callback_query.message.chat_id
        else:
            chatId = update.message.chat_id

        for question in self.task.questions:
            if 'confirmationText' in question:
                formattedConfirmation = question['confirmationText'].format(item=self.temporaryAnswer)
                if question['type'] in questionType.TEXT_BASED_QUESTION_TYPES:
                    bot.send_message(chat_id=chatId, text=formattedConfirmation, parse_mode='Markdown')
                elif question['type'] == questionType.QUESTION_TYPE_IMAGE:
                    image = self.temporaryAnswer[question['property']]
                    bot.send_photo(chat_id=chatId, photo=image, caption=formattedConfirmation, parse_mode='Markdown')
                elif question['type'] == questionType.QUESTION_TYPE_LOCATION:
                    location = self.temporaryAnswer[question['property']]
                    bot.send_message(chat_id=chatId, text=formattedConfirmation, parse_mode='Markdown')
                    bot.send_location(chat_id=chatId, latitude=location['latitude'], longitude=location['longitude'])

        # send is that correct
        replyMarkup = {"keyboard": [[generalCopywriting.YES_BUTTON_TEXT], [generalCopywriting.NO_BUTTON_TEXT]]}
        bot.send_message(chat_id=chatId, text=generalCopywriting.ASK_DATA_CONFIRMATION_TEXT, reply_markup=replyMarkup, parse_mode='Markdown')


    def sendClosingStatement(self, bot, update):
        if update.callback_query:
            chatId = update.callback_query.message.chat_id
        else:
            chatId = update.message.chat_id

        if self.task.type == taskType.TASK_TYPE_CREATE_ITEM:
            formattedClosingStatement = self.task.closingStatement.format(item=self.temporaryAnswer)
        else:
            formattedClosingStatement = self.task.closingStatement.format(item=self.questionData)

        replyMarkup = {"remove_keyboard": True}
        bot.send_message(chat_id=chatId, text=formattedClosingStatement, reply_markup=replyMarkup, parse_mode='Markdown')

    def saveAnswers(self):
        if self.task.type == taskType.TASK_TYPE_CREATE_ITEM: # task type 
            data = self.temporaryAnswer
            data['itemType'] = self.task.itemType
            FirestoreClient.saveDocument('items', data=data)
        elif self.task.type == taskType.TASK_TYPE_VALIDATE_ITEM:
            validations = []
            for question in self.task.questions:
                validations.append({
                    'propertyName': question['property'],
                    'propertyValue': self.questionData[question['property']],
                    'validation': self.temporaryAnswer[question['property']]
                })
            FirestoreClient.updateArrayInDocument('items', self.questionData['_id'], 'validations', validations)
            
