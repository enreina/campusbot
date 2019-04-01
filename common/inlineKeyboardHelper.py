from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def buildInlineKeyboardMarkup(buttons):
    keyboardItems = []
    for button in buttons:
        keyboardItems.append([InlineKeyboardButton(button['text'], callback_data=button['value'])])
    return InlineKeyboardMarkup(keyboardItems)