from google.cloud.firestore_v1beta1.document import DocumentReference 
import firestoreClient as FirestoreClient
from bunch import Bunch
from common.constants.taskType import TASK_TYPE_AS_STRING
from firebase_admin import firestore
from pprint import pprint

TASK_PREVIEW_RULES = {
    'placeTaskInstances': {
        'caption': '{task_instance[task][item][name]}',
        'imageurl': '{task_instance[task][item][imageUrl]}',
        'title': '{task_instance[taskTypeAsString]}',
        'description': '',
        'itemtype': 'Place'
    },
    'foodTaskInstances': {
        'caption': '{task_instance[task][item][name]}',
        'imageurl': '{task_instance[task][item][imageUrl]}',
        'title': '{task_instance[taskTypeAsString]}',
        'description': '',
        'itemtype': 'Food'
    },
    'trashBinTaskInstances': {
        'caption': '{task_instance[task][item][locationDescription]}',
        'imageurl': '{task_instance[task][item][imageUrl]}',
        'title': '{task_instance[taskTypeAsString]}',
        'description': '',
        'itemtype': 'Trash Bin'
    },
    'questionTaskInstances': {
        'caption': '',
        'imageurl': 'http://campusbot.cf/images/blank-white-image.png',
        'title': '{task_instance[task][item][question]}',
        'description': '{task_instance[taskTypeAsString]}',
        'itemtype': '{task_instance[task][item][courseName]}'
    },
}

class TaskInstance(object):
    @staticmethod
    def get_task_instances_for_user(user, taskInstanceCollectionName='placeTaskInstances'):
        if type(user) == dict:
            userId = str(user['_id'])
        else:
            userId = str(user) 
        # get task instances
        task_instances = FirestoreClient.getDocumentsFromSubcollection('users', userId, taskInstanceCollectionName, queries=[('completed','==', False), ('expired', '==', False)], orderBy='createdAt', orderDirection=firestore.Query.ASCENDING, withRef=True)
        # populate task inside each task instance
        for task_instance in task_instances:
            task_instance['task'] = task_instance['task'].get().to_dict()
            task_instance['task']['item'] = task_instance['task']['item'].get().to_dict()

            task_instance['taskTypeAsString'] = TASK_TYPE_AS_STRING[task_instance['task']['type']]
            task_instance['task_preview'] = TaskInstance.build_task_preview(task_instance, taskInstanceCollectionName)

        return [Bunch(task_instance) for task_instance in task_instances]

    @staticmethod
    def build_task_preview(task_instance, taskInstanceCollectionName):
        task_preview = {}
        rules = TASK_PREVIEW_RULES[taskInstanceCollectionName]
        for key,rule in rules.items():
            task_preview[key] = rule.format(task_instance=task_instance)
        
        return task_preview

    @staticmethod
    def update_task_instance(task_instance, data):
        taskInstanceRef = task_instance['_ref']
        taskInstanceRef.update(data)

        



    
