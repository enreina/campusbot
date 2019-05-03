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
from common.constants import taskType, questionType, specialStates, callbackTypes, confirmationStatementTypes
from pprint import pprint
from common.inlineKeyboardHelper import buildInlineKeyboardMarkup, buildTextOfChoiceList, buildRegexFilter, buildAnswerDict
from common import logicJumpHelper
import re
import settings as env
import json
from telegram import ChatAction

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
            elif question['type'] == questionType.QUESTION_TYPE_CATEGORIZATION:
                itemCategory = self.taskTemplate.itemCategory
                subcategories = Category.getSubcategories(itemCategory)
                buttonRows = [{"buttons": [{'text': subcategory['name'], 'value': subcategory['_id']}]} for subcategory in subcategories]
                question['buttonRows'] = buttonRows
                regexRule = buildRegexFilter(buttonRows, withNotSureOption=True)
                handler.append(MessageHandler(Filters.regex(regexRule), self._question_callback))
                question['answerDict'] = buildAnswerDict(buttonRows, withNotSureOption=True)
            elif question['type'] == questionType.QUESTION_TYPE_MULTIPLE_CHOICE_ITEM:
                handler.append(MessageHandler(Filters.text, self._question_callback))
            elif question['type'] == questionType.QUESTION_TYPE_WITH_CUSTOM_BUTTONS or question['type'] == questionType.QUESTION_TYPE_CHECK_COURSE:
                regexRule = buildRegexFilter(question['buttonRows'])
                question['answerDict'] = buildAnswerDict(question['buttonRows'])
                handler.append(MessageHandler(Filters.regex(regexRule), self._question_callback))
                

            if question['type'] == questionType.QUESTION_TYPE_MULTIPLE_CHOICE_ITEM:
                handler.append(MessageHandler(Filters.text, self._question_callback))

            isRequired = 'isRequired' in question and question['isRequired']
            if not isRequired:
                handler.append(CommandHandler('skip', self._skip_question_callback))
            
            states[questionNumber] = handler
        self.numOfStates = len(self.taskTemplate.questions)
        # fallback
        fallbackHandlers = [CommandHandler('quit', self._quit_task_callback)]
        fallbackHandlers.append(MessageHandler(Filters.all, self._fallbackCallback))
        
        conversationName = '{telegramId}-{entryCommand}'.format(telegramId=user['telegramId'], entryCommand=self.entryCommand)
        self.conversationHandler = ConversationHandler(entry_points=entryPoints, states=states, fallbacks=fallbackHandlers, persistent=True, name=conversationName)

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
        choiceText = None

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
            buttonRows = [{'buttons':[buttonRow]} for buttonRow in nearbyPlaces]
            buttonRows.append({'buttons':[{'text': generalCopywriting.NOT_IN_A_BUILDING, 'value': None}]})
            replyMarkup = {"remove_keyboard": True}
            
            # add choice to question text
            choiceText = buildTextOfChoiceList(buttonRows, withNotSureOption=True, withNumber=False)
        elif currentQuestion['type'] in questionType.SINGLE_VALIDATION_QUESTION_TYPES:
            keyboard = [[InlineKeyboardButton(generalCopywriting.VALIDATE_ANSWER_YES_TEXT, callback_data=callbackTypes.VALIDATION_ANSWER_TYPE_YES),
                        InlineKeyboardButton(generalCopywriting.VALIDATE_ANSWER_NO_TEXT, callback_data=callbackTypes.VALIDATION_ANSWER_TYPE_NO)],
                        [InlineKeyboardButton(generalCopywriting.VALIDATE_ANSWER_NOT_SURE_TEXT, callback_data=callbackTypes.VALIDATION_ANSWER_TYPE_NOT_SURE)]]


            replyMarkup = InlineKeyboardMarkup(keyboard)
        elif currentQuestion['type'] == questionType.QUESTION_TYPE_CATEGORIZATION:
            replyMarkup = {"remove_keyboard": True}
            choiceText = buildTextOfChoiceList(currentQuestion['buttonRows'], withNotSureOption=True)
        elif currentQuestion['type'] in [questionType.QUESTION_TYPE_WITH_CUSTOM_BUTTONS, questionType.QUESTION_TYPE_ANSWERS_CONFIRMATION]::
            replyMarkup = {"remove_keyboard": True}
            # add choice to question text
            choiceText = buildTextOfChoiceList(currentQuestion['buttonRows'], withNotSureOption=False)
        elif currentQuestion['type'] == questionType.QUESTION_TYPE_CHECK_COURSE:
            temporaryAnswer['doesCourseExist'] = False
            course = Course.find_course_by_name(temporaryAnswer['courseName'])
            # if course does not exist, move to next question
            if course is None:
                return self.move_to_next_question(update, context)
            temporaryAnswer['course'] = course
            replyMarkup = {"remove_keyboard": True}
            choiceText = buildTextOfChoiceList(currentQuestion['buttonRows'], withNotSureOption=False)
        else:
            replyMarkup = {"remove_keyboard": True}

        # if the question is to theck duplicate
        if 'duplicateCheckProperties' in currentQuestion:
            return self.check_duplicate_item(update, context)

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
            if currentItemIndex >= len(temporaryAnswer[currentQuestion['multiItemPropertyName']]):
                return self.move_to_next_question(update, context)
            item = temporaryAnswer[currentQuestion['multiItemPropertyName']][currentItemIndex]
            formattedQuestion = currentQuestion['text'].format(item=item, idx=currentItemIndex+1)
        else:
            formattedQuestion = currentQuestion['text'].format(item=temporaryAnswer)
        
        # send confirmation text
        if currentQuestion['type'] == questionType.QUESTION_TYPE_ANSWERS_CONFIRMATION:
            confirmationStatements = context.chat_data.get('confirmationStatements', [])
            if not confirmationStatements:
                return self.move_to_next_question(update, context)

            if 'openingText' in currentQuestion:
                message = bot.send_message(chat_id=chatId, text=currentQuestion['openingText'], reply_markup=None, parse_mode='Markdown')
                User.saveUtterance(context.chat_data['userId'], message, byBot=True)
            
            confirmationTextOnly = ""
            for statement in confirmationStatements:
                if statement['type'] == confirmationStatementTypes.CONFIRMATION_STATEMENT_TYPE_TEXT:
                    confirmationTextOnly = "{confirmationTextOnly}{text}\n".format(confirmationTextOnly=confirmationTextOnly, text=statement['text'])
                elif statement['type'] == confirmationStatementTypes.CONFIRMATION_STATEMENT_TYPE_IMAGE:
                    message = bot.send_photo(chat_id=chatId, photo=statement['image'], caption=statement.get('imageCaption', None), parse_mode='Markdown')
                    User.saveUtterance(context.chat_data['userId'], message, byBot=True)
                elif statement['type'] == confirmationStatementTypes.CONFIRMATION_STATEMENT_TYPE_LOCATION:
                    location = statement['location']
                    if 'text' in statement:
                        message = bot.send_message(chat_id=chatId, text=statement['text'], reply_markup=None, parse_mode='Markdown')
                        User.saveUtterance(context.chat_data['userId'], message, byBot=True)
                    message = bot.send_location(chat_id=chatId, latitude=location['latitude'], longitude=location['longitude'])
                    User.saveUtterance(context.chat_data['userId'], message, byBot=True)
            
            if confirmationTextOnly:
                message = bot.send_message(chat_id=chatId, text=confirmationTextOnly, reply_markup=None, parse_mode='Markdown')
                User.saveUtterance(context.chat_data['userId'], message, byBot=True)

        message = bot.send_message(chat_id=chatId, text=formattedQuestion, reply_markup=replyMarkup, parse_mode='Markdown')
        User.saveUtterance(context.chat_data['userId'], message, byBot=True)
        if choiceText is not None:
            message = bot.send_message(chat_id=chatId, text=choiceText, reply_markup=replyMarkup, parse_mode='Markdown')
            User.saveUtterance(context.chat_data['userId'], message, byBot=True)
        
        return currentQuestionNumber

    def send_current_question_response(self, update, context):
        temporaryAnswer = context.chat_data['temporaryAnswer']
        currentQuestionNumber = context.chat_data['currentQuestionNumber']
        currentQuestion = self.taskTemplate.questions[currentQuestionNumber]
        
        if update.callback_query:
            chatId = update.callback_query.message.chat_id
            context.bot.answer_callback_query(update.callback_query.id)
            messageId = update.callback_query.message.message_id
            # disable buttons
            withNotSureOption = currentQuestion['type'] == questionType.QUESTION_TYPE_MULTIPLE_CHOICE_ITEM
            callbackData = json.loads(update.callback_query.data)
            selectedAnswer = callbackData['value']
            replyMarkupDisabled = buildInlineKeyboardMarkup(currentQuestion['buttonRows'], withNotSureOption=withNotSureOption, disabled=True, selectedAnswer=selectedAnswer)
            context.bot.edit_message_reply_markup(chat_id=chatId, message_id=messageId, reply_markup=replyMarkupDisabled)
        else:
            chatId = update.message.chat_id

        if currentQuestion['property'] not in temporaryAnswer:
            return

        # get response based on response button
        for buttonRow in currentQuestion.get('buttonRows', []):
            if isinstance(buttonRow, dict):
                buttons = buttonRow.get('buttons', [])
            else:
                buttons = buttonRow

            for button in buttons:
                if button['value'] == temporaryAnswer[currentQuestion['property']] and 'response' in button:
                    currentQuestion['responseOk'] = button['response']

        if 'responseOk' not in currentQuestion:
            return
        
        if currentQuestion['type'] == questionType.QUESTION_TYPE_CATEGORIZATION:
            if 'category' not in temporaryAnswer or temporaryAnswer['category'] is None:
                formattedResponseOk = currentQuestion['responseNotSure']
            elif 'responseOk' in currentQuestion:
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
            if propertyName == 'name':
                temporaryAnswer['nameLower'] = answer.lower()
        elif typeOfQuestion == questionType.QUESTION_TYPE_NUMBER:
            try:
                answer = int(update.message.text)
            except:
                answer = float(update.message.text)
        elif typeOfQuestion == questionType.QUESTION_TYPE_IMAGE:
            # download image    
            fileName = update.message.photo[-1].file_id
            imageFilePath = '{imagePath}/{fileName}.jpg'.format(imagePath=env.IMAGE_DOWNLOAD_PATH, fileName=fileName)
            imageFile = update.message.photo[-1].get_file().download(custom_path=imageFilePath)
            # upload
            answer = FirestoreClient.upload_blob(imageFilePath, "campusbot/{fileName}".format(fileName=fileName))
            # answer = u'{imageUrlPrefix}/{fileName}.jpg'.format(imageUrlPrefix=env.IMAGE_URL_PREFIX, fileName=fileName)
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
            cleanResponse = update.message.text.lower().encode('ascii', 'ignore').strip()
            callbackData = currentQuestion['answerDict'][cleanResponse]
            if callbackData != callbackTypes.CATEGORIZATION_ANSWER_TYPE_NOT_SURE:
                subcategory = Category.getCategoryById(callbackData)
                answer = subcategory     
                temporaryAnswer['categoryName'] = subcategory['name']
        elif typeOfQuestion in [questionType.QUESTION_TYPE_WITH_CUSTOM_BUTTONS, questionType.QUESTION_TYPE_CHECK_COURSE]:
            cleanResponse = update.message.text.lower().encode('ascii', 'ignore').strip()
            answer = currentQuestion['answerDict'][cleanResponse]
        elif typeOfQuestion == questionType.QUESTION_TYPE_MULTIPLE_CHOICE_ITEM:
            if update.message:
                answer = update.message.text
                if propertyName == 'building':
                    temporaryAnswer['buildingName'] = answer
                    temporaryAnswer['buildingNameLower'] = answer.lower() 
            else:
                callbackData = json.loads(update.callback_query.data)
                if callbackData['value'] is None:
                    answer = None
                    if propertyName == 'building':
                        temporaryAnswer['buildingName'] = generalCopywriting.NOT_IN_A_BUILDING
                        temporaryAnswer['buildingNameLower'] = generalCopywriting.NOT_IN_A_BUILDING.lower()
                elif callbackData['value'] != callbackTypes.GENERAL_ANSWER_TYPE_NOT_SURE:
                    item = Item.getItemById(callbackData['value'], 'placeItems')
                    answer = item
                    if propertyName == 'building':
                        temporaryAnswer['buildingName'] = item['name']
                        temporaryAnswer['buildingNameLower'] = item['name'].lower()      

        if 'multiItemPropertyName' in currentQuestion:
            # handle question with multiple input
            currentItemIndex = context.chat_data['currentItemIndex']
            item = temporaryAnswer[currentQuestion['multiItemPropertyName']][currentItemIndex]
            saveAsArray = 'saveAsArray' in currentQuestion and currentQuestion['saveAsArray']
            if not saveAsArray:
                savedAnswer = {'propertyName': unicode(item), 'propertyValue': answer}
            else:
                if answer is not None and answer:
                    savedAnswer = item
            if propertyName in temporaryAnswer:
                if saveAsArray and answer or not saveAsArray:
                    temporaryAnswer[propertyName].append(savedAnswer)
            else:
                if saveAsArray and answer or not saveAsArray:
                    temporaryAnswer[propertyName] = [savedAnswer]
        else:
            temporaryAnswer[propertyName] = answer

        if temporaryAnswer.get('isDuplicate', False) and 'duplicateItem' in temporaryAnswer:
            temporaryAnswer = temporaryAnswer['duplicateItem'].toDict()
            temporaryAnswer['isDuplicate'] = True
            context.chat_data['temporaryAnswer'] = temporaryAnswer

        # build confirmation statement
        confirmationStatements = context.chat_data.get('confirmationStatements', [])
        if answer is not None and 'confirmationStatement' in currentQuestion:
            statement = currentQuestion['confirmationStatement']
            statementToAppend = statement.copy() 
            if statement['type'] == confirmationStatementTypes.CONFIRMATION_STATEMENT_TYPE_TEXT:
                # get confirmation based on response button
                pprint(currentQuestion.get('buttonRows', []))
                for buttonRow in currentQuestion.get('buttonRows', []):
                    if isinstance(buttonRow, dict):
                        buttons = buttonRow.get('buttons', [])
                    else:
                        buttons = buttonRow

                    for button in buttons:
                        if button['value'] == answer and 'confirmation' in button:
                            statementToAppend['text'] = button['confirmation']

                if 'multiItemPropertyName' in currentQuestion:
                    currentItem = temporaryAnswer[currentQuestion['multiItemPropertyName']][currentItemIndex]
                    statementToAppend['text'] = statementToAppend['text'].format(currentItem=currentItem)
                else:   
                    statementToAppend['text'] = statementToAppend['text'].format(item=temporaryAnswer)
            elif statement['type'] == confirmationStatementTypes.CONFIRMATION_STATEMENT_TYPE_IMAGE:
                if 'imageCaption' in statement:
                    statementToAppend['imageCaption'] = statementToAppend['imageCaption'].format(item=temporaryAnswer)
                statementToAppend['image'] = temporaryAnswer[statementToAppend['imagePropertyName']]
            elif statement['type'] == confirmationStatementTypes.CONFIRMATION_STATEMENT_TYPE_LOCATION:
                statementToAppend['location'] = temporaryAnswer[statementToAppend['locationPropertyName']]
                if 'text' in statementToAppend:
                    statementToAppend['text'] = statementToAppend['text'].format(item=temporaryAnswer)
            
            confirmationStatements.append(statementToAppend)
            context.chat_data['confirmationStatements'] = confirmationStatements
        
        print(confirmationStatements)

        # debugging
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
            message = context.bot.send_message(
                chat_id=chatId, 
                text=formattedClosingStatement, 
                reply_markup=replyMarkup, 
                parse_mode='Markdown',
                disable_web_page_preview=True)
            User.saveUtterance(context.chat_data['userId'], message, byBot=True)

        # offer to start other task
        message = context.bot.send_message(chat_id=chatId, text=generalCopywriting.END_OF_TASK_TEXT, parse_mode='Markdown')
        User.saveUtterance(context.chat_data['userId'], message, byBot=True)
        message = context.bot.send_message(chat_id=chatId, text=generalCopywriting.START_MESSAGE, parse_mode='Markdown')
        User.saveUtterance(context.chat_data['userId'], message, byBot=True)

    def save_answers(self, update, context):
        return
            
    def check_duplicate_item(self, update, context):
        temporaryAnswer = context.chat_data['temporaryAnswer']
        currentQuestionNumber = context.chat_data['currentQuestionNumber']
        currentQuestion = self.taskTemplate.questions[currentQuestionNumber]
        bot = context.bot
        chatId = context.chat_data['chatId']

        # build query to check duplicate
        queries = []
        for propertyName in currentQuestion['duplicateCheckProperties']:
            answer = temporaryAnswer[propertyName]
            if isinstance(answer, dict) and '_ref' in answer:
                answer = answer['_ref']
            queries.append((propertyName, '==', answer))
        potentialDuplicates = FirestoreClient.getDocuments(collectionName=self.itemCollectionName, queries=queries)

        # select the last one from duplicate
        if potentialDuplicates:
            duplicateItem = potentialDuplicates[-1]
            temporaryAnswer['duplicateItem'] = duplicateItem
            # send question
            if isinstance(currentQuestion['text'], list):
                for idx,statement in enumerate(currentQuestion['text']):
                    if idx == (len(currentQuestion['text']) - 1):
                        replyMarkup = buildInlineKeyboardMarkup(currentQuestion['buttonRows'])
                    else:
                        replyMarkup = None

                    if isinstance(statement, dict):
                        if 'imagePropertyName' in statement:
                            image = duplicateItem[statement['imagePropertyName']]
                            caption=None
                            if 'imageCaption' in statement:
                                caption = statement['imageCaption'].format(duplicateItem=duplicateItem)

                            message = bot.send_photo(chat_id=chatId, photo=image, caption=caption, reply_markup=replyMarkup, parse_mode='Markdown')
                            User.saveUtterance(chatId, message, byBot=True)
                        else:
                            formattedText = statement.format(item=temporaryAnswer, duplicateItem=duplicateItem)
                            message = bot.send_message(
                                chat_id=chatId, 
                                text=formattedText, 
                                reply_markup=replyMarkup, 
                                parse_mode='Markdown')
                            User.saveUtterance(chatId, message, byBot=True)
                    else:
                        formattedText = statement.format(item=temporaryAnswer, duplicateItem=duplicateItem)
                        message = bot.send_message(
                            chat_id=chatId,
                            text=formattedText,
                            reply_markup=replyMarkup,
                            parse_mode='Markdown')
                        User.saveUtterance(chatId, message, byBot=True)

            else:
                replyMarkup = buildInlineKeyboardMarkup(currentQuestion['buttonRows'])
                formattedText = currentQuestion['text'].format(item=temporaryAnswer, duplicateItem=duplicateItem)
                message = bot.send_message(
                    chat_id=chatId,
                    text=formattedText,
                    reply_markup=replyMarkup,
                    parse_mode='Markdown')
                User.saveUtterance(chatId, message, byBot=True)
            return currentQuestionNumber
        else:
            return self.move_to_next_question(update, context)
        
    # callbacks
    def _start_task_callback(self, update, context):
        bot = context.bot
        context.chat_data['currentQuestionNumber'] = 0
        context.chat_data['confirmationStatements'] = []
        if update.message:
            User.saveUtterance(update.message.from_user.id, update.message)
            context.chat_data['userId'] = update.message.from_user.id
            context.chat_data['chatId'] = update.message.chat_id
        chatId = context.chat_data['chatId']

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

                    message = bot.send_photo(chat_id=chatId, photo=image, caption=caption, parse_mode='Markdown')
                    User.saveUtterance(context.chat_data['userId'], message, byBot=True)
                if 'jumpRules' in statement:
                    jumpRules = statement['jumpRules']
                    shouldJump, jumpIndex = logicJumpHelper.evaluateJumpRules(item, jumpRules)

                    if shouldJump:
                        context.chat_data['currentQuestionNumber'] = jumpIndex
            else:
                message = bot.send_message(chat_id=chatId, text=statement.format(item=item), parse_mode='Markdown')
                User.saveUtterance(context.chat_data['userId'], message, byBot=True)

        self.send_current_question(update, context)
        return context.chat_data['currentQuestionNumber']
        
    # individual state callback
    def _question_callback(self, update, context):
        if update.message:
            message = update.message
        else:
            message = update.callback_query.message
            if update.callback_query.data == callbackTypes.DISABLED_BUTTON:
                context.bot.answer_callback_query(update.callback_query.id)
                return self._fallbackCallback(update, context)
        
        User.saveUtterance(context.chat_data['userId'], message, callbackQuery=update.callback_query)
        # special callback for confirmation
        currentQuestion = self.taskTemplate.questions[context.chat_data['currentQuestionNumber']]
        if currentQuestion['type'] == questionType.QUESTION_TYPE_ANSWERS_CONFIRMATION:
            return self._answers_confirmation_callback(update, context)
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
        if update.message:
            chatId = update.message.chat_id
            User.saveUtterance(context.chat_data['userId'], update.message)
        else:
            chatId = update.callback_query.message.chat_id
            User.saveUtterance(context.chat_data['userId'], update.callback_query.message)

        currentQuestionNumber = context.chat_data['currentQuestionNumber']
        temporaryAnswer = context.chat_data['temporaryAnswer']
        currentQuestion = self.taskTemplate.questions[currentQuestionNumber]
        formattedResponseError = currentQuestion['responseError'].format(item=temporaryAnswer)
        message = context.bot.send_message(chat_id=chatId, text=formattedResponseError, parse_mode='Markdown')
        User.saveUtterance(chatId, message, byBot=True)

        message = context.bot.send_message(chat_id=chatId, text=generalCopywriting.INSTRUCTION_TO_QUIT_TASK_TEXT, parse_mode='Markdown')
        User.saveUtterance(chatId, message, byBot=True)

        return currentQuestionNumber

    # quit task
    def _quit_task_callback(self, update, context):
        if update.message:
            User.saveUtterance(context.chat_data['userId'], update.message)

        if 'currentTaskInstance' in context.chat_data:
            del context.chat_data['currentTaskInstance']
        self.remove_from_dispatcher()

        chatId = context.chat_data['chatId']

        # offer to start other task
        message = context.bot.send_message(chat_id=chatId, text=generalCopywriting.END_OF_TASK_TEXT, parse_mode='Markdown')
        User.saveUtterance(context.chat_data['userId'], message, byBot=True)
        message = context.bot.send_message(chat_id=chatId, text=generalCopywriting.START_MESSAGE, parse_mode='Markdown')
        User.saveUtterance(context.chat_data['userId'], message, byBot=True)

        return ConversationHandler.END


    # answers confirmation
    def _answers_confirmation_callback(self, update, context):
        callbackData = json.loads(update.callback_query.data)
        selectedAnswer = callbackData['value']
        context.bot.answer_callback_query(update.callback_query.id)
        chatId = update.callback_query.message.chat_id

        # if submitting answers
        if selectedAnswer == callbackTypes.CONFIRM_SUBMIT:
            message = context.bot.send_message(chat_id=chatId, text=generalCopywriting.SUBMITTING_ANSWERS_TEXT, parse_mode='Markdown')
            User.saveUtterance(context.chat_data['userId'], message, byBot=True)
            context.bot.send_chat_action(chatId, ChatAction.TYPING)
            return self.move_to_next_question(update, context)
        # if starting over
        elif selectedAnswer == callbackTypes.CONFIRM_START_OVER:
            context.chat_data['executionStartTime'] = context.chat_data['temporaryAnswer'].get('executionStartTime', None)
            context.chat_data['temporaryAnswer'] = {}
            return self._start_task_callback(update, context)
        # if quitting task
        elif selectedAnswer == callbackTypes.CONFIRM_QUIT:
            return self._quit_task_callback(update, context)

        return self._fallbackCallback(update, context)