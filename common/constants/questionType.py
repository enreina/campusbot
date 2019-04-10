QUESTION_TYPE_TEXT = 0
QUESTION_TYPE_IMAGE = 1
QUESTION_TYPE_LOCATION = 2
QUESTION_TYPE_MULTIPLE_CHOICE_ITEM = 3
QUESTION_TYPE_MULTIPLE_INPUT = 4
QUESTION_TYPE_SINGLE_VALIDATION_TEXT = 5
QUESTION_TYPE_SINGLE_VALIDATION_LOCATION = 6
QUESTION_TYPE_MULTIPLE_VALIDATION = 7
QUESTION_TYPE_CATEGORIZATION = 8
QUESTION_TYPE_WITH_CUSTOM_BUTTONS = 9
QUESTION_TYPE_NUMBER = 10

TEXT_BASED_QUESTION_TYPES = [QUESTION_TYPE_TEXT, QUESTION_TYPE_MULTIPLE_INPUT, QUESTION_TYPE_NUMBER]
SINGLE_VALIDATION_QUESTION_TYPES = [QUESTION_TYPE_SINGLE_VALIDATION_TEXT, QUESTION_TYPE_SINGLE_VALIDATION_LOCATION]
INLINE_BUTTON_BASED_QUESTION_TYPES = [QUESTION_TYPE_SINGLE_VALIDATION_TEXT, QUESTION_TYPE_SINGLE_VALIDATION_LOCATION, QUESTION_TYPE_CATEGORIZATION, QUESTION_TYPE_WITH_CUSTOM_BUTTONS, QUESTION_TYPE_MULTIPLE_CHOICE_ITEM]