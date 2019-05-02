# -*- coding: utf-8 -*-

WELCOME_MESSAGE = '''Hello, welcome to *CampusBot*! With CampusBot, you can share various campus-related knowledge together with other students.'''
START_MESSAGE = '''Try one of these commands to start:

/food - share picture of your meal and rate food on campus 🍔
/place - *Find vacant spots* - Add detailed description about a place on campus 📌
/course - *Learn and let learn* - Have a doubt? Your fellow students can help 📖
/trashbin - *Tide's In- Dirt's Out* - Find trash bins and report trash level 🗑

/help - learn more about this chatbot
'''

HELP_MESSAGE = '''CampusBot is a chatbot that has been built to collect data from students of TU Delft for experimental purposes. It consists of four different domains namely: *Food*, *Place*, *Courses* and *TrashBin*.

1. /food - Share a picture of your meal and also assess and identify items in other pictures.
2. /place - Upload information about several types of places on the TU Delft campus, for example, a study space, a lecture room or a parking space. Also add more information and validate an existing place.
3. /course - Learn and let learn, post any question related to a course at TU Delft, answer a question posted by a fellow student or vote existing answers.
4. /trashbin - Tide’s In- Dirt’s Out: Find trash bins on campus, add detailed information about them and also report the current trash level.

Each of these domains has two kinds of tasks:
- *Enrich*: you would be presented with a picture and asked to add detailed information about it.
- *Validate*: you would be asked to assess the already available information.

You can also *Create* a new item in each domain.

_Please note that the data would only be used for experimental purposes and your personal data would not be disclosed anywhere._
'''

SEND_LOCATION_TEXT = "Send My Location 📍"

ASK_DATA_CONFIRMATION_TEXT = "Is that correct?"

YES_BUTTON_TEXT = "Yes 👍"
NO_BUTTON_TEXT = "No 👎"

VALIDATE_ANSWER_YES_TEXT = "Yes 👍"
VALIDATE_ANSWER_NO_TEXT = "No 👎"
VALIDATE_ANSWER_NOT_SURE_TEXT = "Not sure 🤔"
VALIDATE_ANSWER_KEYBOARD = [[VALIDATE_ANSWER_YES_TEXT], [VALIDATE_ANSWER_NO_TEXT], [VALIDATE_ANSWER_NOT_SURE_TEXT]]

GENERAL_NOT_SURE_TEXT = "Not sure 🤔"

NO_TASK_INSTANCES_AVAILABLE = '''There is no task for *{canonical_name}* right now 🙁. 
Fancy to try other commands?'''

LOADING_TASKS_TEXT = "Please wait a moment as your tasks are being loaded..⏳"
END_OF_TASK_TEXT = "Would you like to do another task?"

INSTRUCTION_TO_QUIT_TASK_TEXT = "If you want to end this current task without submitting your answers, type /quit"