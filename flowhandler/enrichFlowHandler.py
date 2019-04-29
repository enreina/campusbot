from genericFlowHandler import GenericFlowHandler
from datetime import datetime
from dateutil.tz import tzlocal
import db.firestoreClient as FirestoreClient
from db.taskInstance import TaskInstance
from db.user import User
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
        self.canonicalName = canonicalName
        super(EnrichFlowHandler, self).__init__(taskTemplateId, dispatcher, itemCollectionName=itemCollectionName, entryCommand=entryCommand)


    '''
    override save answers method
    '''
    def save_answers(self, update, context):
        user = context.chat_data['user']
        taskInstance = context.chat_data['currentTaskInstance']
        temporaryAnswer = context.chat_data['temporaryAnswer']

        data = {}
        for question in self.taskTemplate.questions:
            propertyName = question['property']
            if propertyName in temporaryAnswer:
                value = temporaryAnswer[propertyName]
                if isinstance(value, dict) and '_ref' in value:
                    data[propertyName] = value['_ref']
                else:
                    data[propertyName] = value

        data['taskInstanceId'] = taskInstance['_id']
        data['taskInstance'] = taskInstance['_ref']
        data['createdAt'] = datetime.now(tzlocal())

        FirestoreClient.saveDocument(self.itemCollectionName, data=data)
        # TO-DO: update taskInstance.completed and task count of user
        TaskInstance.update_task_instance(taskInstance, {'completed': True})
        user['totalTasksCompleted'][self.canonicalName.lower()] = user['totalTasksCompleted'][self.canonicalName.lower()] + 1
        User.updateUser(user['_id'], {'totalTasksCompleted': user['totalTasksCompleted']})


    def _start_task_callback(self, update, context):
        context.chat_data['currentTaskInstance'] = self.taskInstance
        context.chat_data['temporaryAnswer'] = self.taskInstance['task']['item']
        context.chat_data['temporaryAnswer']['executionStartTime'] = datetime.now(tzlocal())
        questionNumber = super(EnrichFlowHandler, self)._start_task_callback(update, context)

        return questionNumber
