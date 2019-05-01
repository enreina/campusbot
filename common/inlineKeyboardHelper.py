# -*- coding: utf-8 -*-
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import json 
from dialoguemanager.response import generalCopywriting
from common.constants import callbackTypes
import re

def buildInlineKeyboardMarkup(buttonRows, withNotSureOption=False, disabled=False, selectedAnswer=None):
    keyboardItems = []
    for buttonRow in buttonRows:
        inlineKeyboardButtonRow = []
        buttons = []
        if isinstance(buttonRow, dict) and 'buttons' in buttonRow:
            buttons = buttonRow['buttons']
        elif isinstance(buttonRow, list):
            buttons = buttonRow
        
        for button in buttons:
            if disabled:
                callbackDataInJson = callbackTypes.DISABLED_BUTTON
            else:
                callbackDataInJson = json.dumps({'value': button['value']})
            text = button['text']
            if disabled and selectedAnswer == button['value']:
                text = u"{text} ✅".format(text=text)
            inlineKeyboardButtonRow.append(InlineKeyboardButton(text, callback_data=callbackDataInJson))
        keyboardItems.append(inlineKeyboardButtonRow)

    if withNotSureOption:
        if disabled:
            callbackDataInJson = callbackTypes.DISABLED_BUTTON
        else:
            callbackDataInJson = json.dumps({'value': callbackTypes.GENERAL_ANSWER_TYPE_NOT_SURE})
        text = generalCopywriting.GENERAL_NOT_SURE_TEXT
        if disabled and selectedAnswer == button['value']:
            text = u"{text} ✅".format(text=text)
        keyboardItems.append([InlineKeyboardButton(text, callback_data=callbackDataInJson)])

    return InlineKeyboardMarkup(keyboardItems)

def buildTextOfChoiceList(buttonRows, withNotSureOption=False, withNumber=True):
    idx = 0
    message = ""

    for buttonRow in buttonRows:
        for button in buttonRow['buttons']:
            idx = idx + 1
            if withNumber:
                message = '''{message}{num}. {choice}\n'''.format(message=message, num=str(idx), choice=button['text'])
            else:
                message = '''{message}- {choice}\n'''.format(message=message, choice=button['text'])
    
    if withNotSureOption:
        idx = idx + 1
        if withNumber:
            message = '''{message}{num}. {choice}\n'''.format(message=message, num=str(idx), choice=generalCopywriting.GENERAL_NOT_SURE_TEXT)
        else:
            message = '''{message}- {choice}\n'''.format(message=message, choice=generalCopywriting.GENERAL_NOT_SURE_TEXT)

    
    if withNumber:
        message = '''{message}\n_You can choose the answer by typing the number or the answer_'''.format(message=message)
    else:
        message = '''{message}\n_You can choose the answer by typing the answer_'''.format(message=message)
    
    return message

def buildRegexFilter(buttonRows):
    matchesList = []
    idx = 0
    for buttonRow in buttonRows:
        for button in buttonRow['buttons']:
            idx = idx + 1
            matchesList.append(str(idx))
            matchesList.append(button['text'].encode('ascii', 'ignore').strip())
    return re.compile("^\s*({matches})\s*$".format(matches="|".join(matchesList)), re.I)

def buildAnswerDict(buttonRows):
    answerDict = {}
    idx = 0
    for buttonRow in buttonRows:
        for button in buttonRow['buttons']:
            idx = idx + 1
            answerDict[str(idx)] = button['value']
            textWithoutEmoji = button['text'].lower().encode('ascii', 'ignore').strip()
            text = button['text'].lower().strip()
            answerDict[textWithoutEmoji] = button['value']
            if text != textWithoutEmoji:
                answerDict[text] = button['value']


    return answerDict



    
            