from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import json 
from dialoguemanager.response import generalCopywriting
from common.constants import callbackTypes

def buildInlineKeyboardMarkup(buttonRows, withNotSureOption=False):
    keyboardItems = []
    for buttonRow in buttonRows:
        inlineKeyboardButtonRow = []
        buttons = []
        if isinstance(buttonRow, dict) and 'buttons' in buttonRow:
            buttons = buttonRow['buttons']
        elif isinstance(buttonRow, list):
            buttons = buttonRow
        
        for button in buttons:
            callbackDataInJson = json.dumps({'value': button['value']})
            inlineKeyboardButtonRow.append(InlineKeyboardButton(button['text'], callback_data=callbackDataInJson))
        keyboardItems.append(inlineKeyboardButtonRow)

    if withNotSureOption:
        callbackDataInJson = json.dumps({'value': callbackTypes.GENERAL_ANSWER_TYPE_NOT_SURE})
        keyboardItems.append([InlineKeyboardButton(generalCopywriting.GENERAL_NOT_SURE_TEXT, callback_data=callbackDataInJson)])

    return InlineKeyboardMarkup(keyboardItems)