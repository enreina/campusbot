import db.firestoreClient as FirestoreClient
import datetime
from google.cloud import firestore
from db.taskTemplate import TaskTemplate
import json
from pprint import pprint
from google.cloud.firestore_v1beta1.document import DocumentReference
from db.firestoreClient import db

# taskTemplateCreatePlace = TaskTemplate.getTaskTemplateById('create-trashbin')
# questions = taskTemplateCreatePlace['questions']

# FirestoreClient.updateDocument('taskTemplates', 'enrich-trashbin', {'questions': questions})

# template = TaskTemplate.getTaskTemplateById('validate-food')
# questions = template['questions']
# questions.append(questions[0])
# questions.append(questions[0])

# FirestoreClient.updateDocument('taskTemplates', 'validate-food', {'questions': questions})

# get place task instances
questionTaskInstances = db.collection('questionTaskInstances').get()
taskInstancesRef = db.collection('users').document('156992599').collection('questionTaskInstances')
for instance in questionTaskInstances:
    taskInstancesRef.add(instance.to_dict())