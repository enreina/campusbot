import firestoreClient as FirestoreClient

class Task(object):

    def __init__(self, openingStatement, closingStatement, taskType, entryCommand=None, questions=[]):
        self.openingStatement = openingStatement
        self.closingStatement = closingStatement
        self.type = taskType
        self.entryCommand = entryCommand
        self.questions = questions

    @staticmethod
    def getTaskById(taskId):
        taskDictionary = FirestoreClient.getDocument('tasks', taskId, populate=True)
        return Task(taskDictionary['openingStatement'], taskDictionary['closingStatement'], taskDictionary['type'], taskDictionary['entryCommand'], taskDictionary['questions'])

    
