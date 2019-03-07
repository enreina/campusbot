import firestoreClient as FirestoreClient
from bunch import Bunch

class Task(object):
    @staticmethod
    def getTaskById(taskId):
        taskDictionary = FirestoreClient.getDocument('tasks', taskId, populate=False)
        return Bunch(taskDictionary)

    
