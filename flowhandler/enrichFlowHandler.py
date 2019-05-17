from genericFlowHandler import GenericFlowHandler
from datetime import datetime
from dateutil.tz import tzlocal
import db.firestoreClient as FirestoreClient
from db.taskInstance import TaskInstance
from db.user import User
from pprint import pprint
import common.campusbotApi as CampusBotApi

class EnrichFlowHandler(GenericFlowHandler):
    '''
    Flow handler for 'enrich' task

    Attributes:
        canonicalName: name of the use case
        dispatcher: the dispatcher used to handle telegram bot updates
    '''
    def __init__(self, canonicalName, itemCollectionName, dispatcher, entryCommand, taskInstance, itemCollectionNamePrefix):
        taskTemplateId = 'enrich-{canonicalName}'.format(canonicalName=canonicalName.lower())
        self.taskInstance = taskInstance
        self.itemCollectionNamePrefix = itemCollectionNamePrefix
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
            if 'property' not in question:
                continue
            propertyName = question['property']
            if propertyName in temporaryAnswer:
                value = temporaryAnswer[propertyName]
                
                if propertyName == 'building' and value is not None:
                    if isinstance(value, basestring): 
                        name = value
                    else:
                        name = value['name']
                    data['buildingName'] = name
                    data['buildingNameLower'] = name.lower()

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
        user['totalTasksCompleted'][self.itemCollectionNamePrefix.lower()] = user['totalTasksCompleted'][self.itemCollectionNamePrefix.lower()] + 1
        tasksCompleted = user['tasksCompleted']
        tasksCompleted.append({'activeDate': data['createdAt']})
        User.updateUser(user['_id'], {
            'totalTasksCompleted': user['totalTasksCompleted'], 
            'tasksCompleted': tasksCompleted
        })

        if 'buildingName' in temporaryAnswer:
            User.updatePreferredLocationNames(
                user['_id'],
                temporaryAnswer['buildingName'].lower()
            )

        if 'courseName' in temporaryAnswer:
            User.updatePreferredCourses(
                user['_id'],
                temporaryAnswer['courseName'].lower()
            )

        # create validation task
        CampusBotApi.generate_validation_task(self.itemCollectionNamePrefix.lower(), userId=user['_id'], enrichmentTaskInstanceId=taskInstance['_id'])
        

    def _start_task_callback(self, update, context):
        context.chat_data['currentTaskInstance'] = self.taskInstance
        context.chat_data['temporaryAnswer'] = self.taskInstance['task']['item'].copy()
        context.chat_data['temporaryAnswer']['executionStartTime'] = datetime.now(tzlocal())
        questionNumber = super(EnrichFlowHandler, self)._start_task_callback(update, context)

        return questionNumber
