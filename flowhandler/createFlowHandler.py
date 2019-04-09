from genericFlowHandler import GenericFlowHandler
from datetime import datetime
from dateutil.tz import tzlocal
import db.firestoreClient as FirestoreClient

class CreateFlowHandler(GenericFlowHandler):
    '''
    Flow handler for 'create' task

    Attributes:
        canonicalName: name of the use case
        dispatcher: the dispatcher used to handle telegram bot updates
    '''
    def __init__(self, canonicalName, itemCollectionName, dispatcher):
        taskTemplateId = 'create-{canonicalName}'.format(canonicalName=canonicalName.lower())
        super(CreateFlowHandler, self).__init__(taskTemplateId, dispatcher, itemCollectionName=itemCollectionName)


    '''
    override save answers method
    '''
    def save_answers(self, temporaryAnswer, user):
        data = temporaryAnswer
        for key,value in temporaryAnswer.items():
            if '_ref' in value:
                temporaryAnswer[key] = value['_ref']

        data['authorId'] = user['_id']
        data['author'] = user['_ref']
        data['createdAt'] = datetime.now(tzlocal())

        FirestoreClient.saveDocument(self.itemCollectionName, data=data)

    def _start_task_callback(self, update, context):
        questionNumber = super(CreateFlowHandler, self)._start_task_callback(update, context)
        context.chat_data['currentTaskInstance'] = {}
        
        return questionNumber
