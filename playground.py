import db.firestoreClient as FirestoreClient
import datetime
from google.cloud import firestore
from db.taskTemplate import TaskTemplate
import json
from pprint import pprint
from google.cloud.firestore_v1beta1.document import DocumentReference


taskTemplateCreatePlace = TaskTemplate.getTaskTemplateById('create-place')
questions = taskTemplateCreatePlace['questions']

FirestoreClient.updateDocument('taskTemplates', 'enrich-place-test', {'questions': questions})

