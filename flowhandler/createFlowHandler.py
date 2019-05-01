from genericFlowHandler import GenericFlowHandler
from datetime import datetime
from dateutil.tz import tzlocal
import db.firestoreClient as FirestoreClient
from db.course import Course
from db.user import User
from pprint import pprint

class CreateFlowHandler(GenericFlowHandler):
    '''
    Flow handler for 'create' task

    Attributes:
        canonicalName: name of the use case
        dispatcher: the dispatcher used to handle telegram bot updates
    '''
    def __init__(self, canonicalName, itemCollectionName, dispatcher):
        self.canonicalName = canonicalName
        taskTemplateId = 'create-{canonicalName}'.format(canonicalName=canonicalName.lower())
        super(CreateFlowHandler, self).__init__(taskTemplateId, dispatcher, itemCollectionName=itemCollectionName)


    '''
    override save answers method
    '''
    def save_answers(self, update, context):
        data = context.chat_data['temporaryAnswer']
        user = context.chat_data['user']
        for key,value in data.items():
            if key == 'building' and value is not None:
                if isinstance(value, str): 
                    name = value
                else:
                    name = value['name']
                data['buildingName'] = name
                data['buildingNameLower'] = name.lower()
            if isinstance(value, dict) and '_ref' in value:
                data[key] = value['_ref']

        data['authorId'] = user['_id']
        data['author'] = user['_ref']
        data['createdAt'] = datetime.now(tzlocal())

        if 'doesCourseExist' in data:
            if not data['doesCourseExist']:
                if 'courseCode' not in data:
                    data['courseCode'] = None
                data['course'] = Course.find_or_create_course_ref(data['courseCode'], data['courseName'])

        FirestoreClient.saveDocument(self.itemCollectionName, data=data)
        # update tasks completed
        user['totalTasksCompleted'][self.canonicalName.lower()] = user['totalTasksCompleted'][self.canonicalName.lower()] + 1
        tasksCompleted = user['tasksCompleted']
        tasksCompleted.append({'activeDate': data['createdAt']})
        User.updateUser(user['_id'], {
            'totalTasksCompleted': user['totalTasksCompleted'], 
            'tasksCompleted': tasksCompleted
        })

    def _start_task_callback(self, update, context):
        questionNumber = super(CreateFlowHandler, self)._start_task_callback(update, context)
        context.chat_data['currentTaskInstance'] = {}
        context.chat_data['temporaryAnswer'] = {
            'executionStartTime': datetime.now(tzlocal())
        }
        
        return questionNumber
