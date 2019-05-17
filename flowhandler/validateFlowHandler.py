from genericFlowHandler import GenericFlowHandler
from datetime import datetime
from dateutil.tz import tzlocal
import db.firestoreClient as FirestoreClient
from db.course import Course
from pprint import pprint
from db.taskInstance import TaskInstance
from db.user import User

class ValidateFlowHandler(GenericFlowHandler):
    '''
    Flow handler for 'enrich' task

    Attributes:
        canonicalName: name of the use case
        dispatcher: the dispatcher used to handle telegram bot updates
    '''
    def __init__(self, canonicalName, itemCollectionName, dispatcher, entryCommand, taskInstance, itemCollectionNamePrefix):
        taskTemplateId = 'validate-{canonicalName}'.format(canonicalName=canonicalName.lower())
        self.itemCollectionNamePrefix = itemCollectionNamePrefix
        self.taskInstance = taskInstance
        super(ValidateFlowHandler, self).__init__(taskTemplateId, dispatcher, itemCollectionName=itemCollectionName, entryCommand=entryCommand)


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
                if isinstance(value, dict) and '_ref' in value:
                    data[propertyName] = value['_ref']
                else:
                    data[propertyName] = value

        data['taskInstanceId'] = taskInstance['_id']
        data['taskInstance'] = taskInstance['_ref']
        data['createdAt'] = datetime.now(tzlocal())

        FirestoreClient.saveDocument(self.itemCollectionName, data=data)
        # TO-DO: update task count of user
        # TO-DO: update taskInstance.completed and task count of user
        TaskInstance.update_task_instance(taskInstance, {'completed': True})
        user['totalTasksCompleted'][self.itemCollectionNamePrefix.lower()] = user['totalTasksCompleted'][self.itemCollectionNamePrefix.lower()] + 1
        tasksCompleted = user['tasksCompleted']
        tasksCompleted.append({'activeDate': data['createdAt']})
        User.updateUser(user['_id'], {
            'totalTasksCompleted': user['totalTasksCompleted'], 
            'tasksCompleted': tasksCompleted
        })

        if 'building' in temporaryAnswer:
            User.updatePreferredLocationNames(
                user['_id'],
                temporaryAnswer['building'].lower()
            )
        if 'courseName' in temporaryAnswer:
            User.updatePreferredCourses(
                user['_id'],
                temporaryAnswer['courseName'].lower()
            )

    def _start_task_callback(self, update, context):
        context.chat_data['currentTaskInstance'] = self.taskInstance
        context.chat_data['temporaryAnswer'] = self.taskInstance['task']['aggregatedAnswers'].copy()
        context.chat_data['temporaryAnswer']['executionStartTime'] = datetime.now(tzlocal())
        questionNumber = super(ValidateFlowHandler, self)._start_task_callback(update, context)

        return questionNumber

    def send_current_question(self, update, context):
        questionNumber = super(ValidateFlowHandler, self).send_current_question(update, context)
        temporaryAnswer = context.chat_data['temporaryAnswer']
        return questionNumber