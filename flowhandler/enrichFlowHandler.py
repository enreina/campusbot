from genericFlowHandler import GenericFlowHandler
from datetime import datetime
from dateutil.tz import tzlocal
import db.firestoreClient as FirestoreClient
from db.course import Course

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
    def save_answers(self, temporaryAnswer, user):
        data = temporaryAnswer
        for key,value in temporaryAnswer.items():
            if isinstance(value, dict) and '_ref' in value:
                temporaryAnswer[key] = value['_ref']

        data['authorId'] = user['_id']
        data['author'] = user['_ref']
        data['createdAt'] = datetime.now(tzlocal())

        if 'doesCourseExist' in temporaryAnswer:
            if not temporaryAnswer['doesCourseExist']:
                if 'courseCode' not in data:
                    data['courseCode'] = None
                data['course'] = Course.find_or_create_course_ref(data['courseCode'], data['courseName'])

        FirestoreClient.saveDocument(self.itemCollectionName, data=data)

    def _start_task_callback(self, update, context):
        questionNumber = super(EnrichFlowHandler, self)._start_task_callback(update, context)
        context.chat_data['currentTaskInstance'] = self.taskInstance
        
        return questionNumber
