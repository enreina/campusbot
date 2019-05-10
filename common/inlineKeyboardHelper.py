# -*- coding: utf-8 -*-
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import json 
from dialoguemanager.response import generalCopywriting
from common.constants import callbackTypes

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