from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import json 

def buildInlineKeyboardMarkup(buttonRows):
    keyboardItems = []
    for buttonRow in buttonRows:
        inlineKeyboardButtonRow = []
        for button in buttonRow['buttons']:
            callbackDataInJson = json.dumps({'value': button['value']})
            inlineKeyboardButtonRow.append(InlineKeyboardButton(button['text'], callback_data=callbackDataInJson))
        keyboardItems.append(inlineKeyboardButtonRow)
    return InlineKeyboardMarkup(keyboardItems)