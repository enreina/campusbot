import firestoreClient as FirestoreClient

class Task(object):

    def __init__(self, openingStatement, closingStatement, taskType, entryCommand=None, questions=[], itemType=None):
        self.openingStatement = openingStatement
        self.closingStatement = closingStatement
        self.type = taskType
        self.entryCommand = entryCommand
        self.questions = questions
        self.itemType = itemType

    @staticmethod
    def getTaskById(taskId):
        taskDictionary = FirestoreClient.getDocument('tasks', taskId, populate=False)
        return Task(taskDictionary['openingStatement'], taskDictionary['closingStatement'], taskDictionary['type'], taskDictionary['entryCommand'], taskDictionary['questions'], taskDictionary['itemType'])

    
