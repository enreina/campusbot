import firestoreClient as FirestoreClient
from bunch import Bunch

class TaskTemplate(object):
    @staticmethod
    def getTaskTemplateById(taskTemplateId):
        taskTemplate = FirestoreClient.getDocument('taskTemplates', taskTemplateId, populate=False)
        return Bunch(taskTemplate)

    
