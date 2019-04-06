from google.cloud.firestore_v1beta1.document import DocumentReference 
import firestoreClient as FirestoreClient
from bunch import Bunch
from common.constants.taskType import TASK_TYPE_AS_STRING

class TaskInstance(object):
    @staticmethod
    def get_task_instances_for_user(user, task_instance_collection_name='placeTaskInstances'):
        if type(user) == dict:
            userId = user['_id']
        else:
            userId = user 
        # get task instances
        task_instances = FirestoreClient.getDocuments(task_instance_collection_name, [
            ('userId', '==', userId)])
        # populate task inside each task instance
        for task_instance in task_instances:
            task_instance['task'] = task_instance['task'].get().to_dict()
            task_instance['task']['item'] = task_instance['task']['item'].get().to_dict()

            task_instance['title'] = task_instance['task']['item']['name'] # for place
            task_instance['taskTypeAsString'] = TASK_TYPE_AS_STRING[task_instance['task']['type']]
             
        return [Bunch(task_instance) for task_instance in task_instances]

    
