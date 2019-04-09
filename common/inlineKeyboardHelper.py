from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import json 

def buildInlineKeyboardMarkup(buttonRows):
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
    return InlineKeyboardMarkup(keyboardItems)