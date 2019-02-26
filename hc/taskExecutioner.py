from db.task import Task
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler
from dialoguemanager.response import generalCopywriting

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

    def initConversationHandler(self):
        # entry points
        def startTask(bot, update):
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
            if self.currentQuestionNumber >= len(self.task.questions):
                self.currentQuestionNumber = ConversationHandler.END
                bot.send_message(chat_id=update.message.chat_id, text=self.task.closingStatement, parse_mode='Markdown')
            else:
                self.sendCurrentQuestion(bot, update)

            return self.currentQuestionNumber

        states = {}
        for questionNumber, question in enumerate(self.task.questions):
            # create handler
            if question['type'] == 'image':
                handler = MessageHandler(Filters.photo, questionHandler)
            elif question['type'] == 'location':
                handler = MessageHandler(Filters.location, questionHandler)
            elif question['type'] == 'text':
                handler = MessageHandler(Filters.text, questionHandler)
            states[questionNumber] = [handler]

        # fallback
        def fallback(bot, update):
            currentQuestion = self.task.questions[self.currentQuestionNumber]
            bot.send_message(chat_id=update.message.chat_id, text=currentQuestion['responseError'], parse_mode='Markdown')

            return self.currentQuestionNumber

        self.conversationHandler = ConversationHandler(entry_points=entryPoints, states=states, fallbacks=[MessageHandler(Filters.all, fallback)])


    def sendCurrentQuestion(self, bot, update):
        currentQuestion = self.task.questions[self.currentQuestionNumber]
        if currentQuestion['type'] == 'location':
            replyMarkup = {"keyboard": [[{"text": generalCopywriting.SEND_LOCATION_TEXT, "request_location": True}]]}
        else:
            replyMarkup = {"remove_keyboard": True}

        bot.send_message(chat_id=update.message.chat_id, text=currentQuestion['text'], reply_markup=replyMarkup, parse_mode='Markdown')

    def sendCurrentQuestionResponse(self, bot, update):
        currentQuestion = self.task.questions[self.currentQuestionNumber]
        bot.send_message(chat_id=update.message.chat_id, text=currentQuestion['responseOk'], parse_mode='Markdown')

    def saveTemporaryAnswer(self, bot, update):
        currentQuestion = self.task.questions[self.currentQuestionNumber]
        if currentQuestion['type'] == 'text':
            self.temporaryAnswer[currentQuestion['property']] = update.message.text
        elif currentQuestion['type'] == 'image':
            self.temporaryAnswer[currentQuestion['property']] = update.message.photo[0].file_id
        elif currentQuestion['type'] == 'location':
            self.temporaryAnswer[currentQuestion['property']] = update.message.location

        print(self.temporaryAnswer)
        