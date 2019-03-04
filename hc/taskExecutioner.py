from db.task import Task
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler
from dialoguemanager.response import generalCopywriting
import db.firestoreClient as FirestoreClient
from utility.placeUtility import findNearestPlaceItem

class TaskExecutioner(object):
    '''Execute a certain task

    Attributes:
        task: the task data loaded from database
        currentQuestionNumber: the current state (question number) of executing the task
    '''
    TASK_TYPE_CREATE_ITEM = 0

    def __init__(self, taskId):
        self.task = Task.getTaskById(taskId) # load task from db
        self.currentQuestionNumber = 0 # start from opening statement
        self.temporaryAnswer = {}
        self.initConversationHandler()

    def initConversationHandler(self):
        # entry points
        def startTask(bot, update):
            self.currentQuestionNumber = 0

            bot.send_message(chat_id=update.message.chat_id, text=self.task.openingStatement, parse_mode='Markdown')
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
            if question['type'] == 'image':
                handler = MessageHandler(Filters.photo, questionHandler)
            elif question['type'] == 'location':
                handler = MessageHandler(Filters.location, questionHandler)
            elif question['type'] in ['text', 'multiple-input', 'location-name']:
                handler = MessageHandler(Filters.text, questionHandler)
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


    def sendCurrentQuestion(self, bot, update):
        currentQuestion = self.task.questions[self.currentQuestionNumber]
        formattedQuestion = currentQuestion['text'].format(item=self.temporaryAnswer)

        if currentQuestion['type'] == 'location':
            replyMarkup = {"keyboard": [[{"text": generalCopywriting.SEND_LOCATION_TEXT, "request_location": True}]]}
        elif currentQuestion['type'] == 'location-name':
            locationAnswer = self.temporaryAnswer['location']
            # find nearby places
            nearbyPlaces = findNearestPlaceItem(locationAnswer['latitude'], locationAnswer['longitude'])
            print(nearbyPlaces)
            # construct keyboard for reply
            keyboardReply = []
            for place in nearbyPlaces:
                keyboardReply.append([place['name']])
            replyMarkup = {"keyboard": keyboardReply}
        else:
            replyMarkup = {"remove_keyboard": True}

        bot.send_message(chat_id=update.message.chat_id, text=formattedQuestion, reply_markup=replyMarkup, parse_mode='Markdown')

    def sendCurrentQuestionResponse(self, bot, update):
        currentQuestion = self.task.questions[self.currentQuestionNumber]
        formattedResponseOk = currentQuestion['responseOk'].format(item=self.temporaryAnswer)
        replyMarkup = {"remove_keyboard": True}
        bot.send_message(chat_id=update.message.chat_id, text=formattedResponseOk, reply_markup=replyMarkup, parse_mode='Markdown')

    def saveTemporaryAnswer(self, bot, update):
        currentQuestion = self.task.questions[self.currentQuestionNumber]
        propertyName = currentQuestion['property']
        if currentQuestion['type'] in ['text', 'location-name']:
            self.temporaryAnswer[propertyName] = update.message.text
        elif currentQuestion['type'] == 'image':
            self.temporaryAnswer[propertyName] = update.message.photo[0].file_id
        elif currentQuestion['type'] == 'location':
            self.temporaryAnswer[propertyName] = {'latitude': update.message.location.latitude, 'longitude': update.message.location.longitude}
        elif currentQuestion['type'] == 'multiple-input':
            splittedAnswers = [x.strip() for x in update.message.text.split(',')]
            self.temporaryAnswer[propertyName] = update.message.text
            self.temporaryAnswer[propertyName + '-list'] = splittedAnswers
        
    def sendConfirmation(self, bot, update):
        for question in self.task.questions:
            if 'confirmationText' in question:
                formattedConfirmation = question['confirmationText'].format(item=self.temporaryAnswer)
                if question['type'] in ['text', 'multiple-input', 'location-name']:
                    bot.send_message(chat_id=update.message.chat_id, text=formattedConfirmation, parse_mode='Markdown')
                elif question['type'] == 'image':
                    image = self.temporaryAnswer[question['property']]
                    bot.send_photo(chat_id=update.message.chat_id, photo=image, caption=formattedConfirmation, parse_mode='Markdown')
                elif question['type'] == 'location':
                    location = self.temporaryAnswer[question['property']]
                    bot.send_message(chat_id=update.message.chat_id, text=formattedConfirmation, parse_mode='Markdown')
                    bot.send_location(chat_id=update.message.chat_id, latitude=location['latitude'], longitude=location['longitude'])
        # send is that correct
        replyMarkup = {"keyboard": [[generalCopywriting.YES_BUTTON_TEXT], [generalCopywriting.NO_BUTTON_TEXT]]}
        bot.send_message(chat_id=update.message.chat_id, text=generalCopywriting.ASK_DATA_CONFIRMATION_TEXT, reply_markup=replyMarkup, parse_mode='Markdown')


    def sendClosingStatement(self, bot, update):
        formattedClosingStatement = self.task.closingStatement.format(item=self.temporaryAnswer)
        replyMarkup = {"remove_keyboard": True}
        bot.send_message(chat_id=update.message.chat_id, text=formattedClosingStatement, reply_markup=replyMarkup, parse_mode='Markdown')

    def saveAnswers(self):
        if self.task.type == self.TASK_TYPE_CREATE_ITEM: # task type 
            data = self.temporaryAnswer
            data['itemType'] = self.task.itemType
            FirestoreClient.saveDocument('items', data=data)

