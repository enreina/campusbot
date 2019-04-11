from genericFlowHandler import GenericFlowHandler
from datetime import datetime
from dateutil.tz import tzlocal
import db.firestoreClient as FirestoreClient
from db.course import Course
from pprint import pprint

class EnrichFlowHandler(GenericFlowHandler):
    '''
    Flow handler for 'enrich' task

    Attributes:
        canonicalName: name of the use case
        dispatcher: the dispatcher used to handle telegram bot updates
    '''
    def __init__(self, canonicalName, itemCollectionName, dispatcher, entryCommand, taskInstance):
        taskTemplateId = 'enrich-{canonicalName}'.format(canonicalName=canonicalName.lower())
        self.taskInstance = taskInstance
        super(EnrichFlowHandler, self).__init__(taskTemplateId, dispatcher, itemCollectionName=itemCollectionName, entryCommand=entryCommand)


    '''
    override save answers method
    '''
    def save_answers(self, update, context):
        data = context.chat_data['temporaryAnswer']
        user = context.chat_data['user']
        taskInstance = context.chat_data['currentTaskInstance']
        for key,value in temporaryAnswer.items():
            if isinstance(value, dict) and '_ref' in value:
                temporaryAnswer[key] = value['_ref']
        
        data['taskId'] = taskInstance.task['_id']
        data['task'] = taskInstance.task['_ref']
        data['taskInstanceId'] = taskInstance['_id']
        data['taskInstance'] = taskInstance['_ref']
        data['createdAt'] = datetime.now(tzlocal())

        FirestoreClient.saveDocument(self.itemCollectionName, data=data)

    def _start_task_callback(self, update, context):
        context.chat_data['currentTaskInstance'] = self.taskInstance
        context.chat_data['temporaryAnswer'] = self.taskInstance.task['item']
        context.chat_data['temporaryAnswer']['executionStartTime'] = datetime.now(tzlocal())
        questionNumber = super(EnrichFlowHandler, self)._start_task_callback(update, context)

        return questionNumber
