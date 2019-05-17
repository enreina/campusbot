import db.firestoreClient as FirestoreClient
import datetime
from google.cloud import firestore
from db.taskTemplate import TaskTemplate
import json
from pprint import pprint
from google.cloud.firestore_v1beta1.document import DocumentReference
from db.firestoreClient import db

# copy user
# user = db.collection('users').document('156992599').get()
# db.collection('users').document('156992599_bak').set(user.to_dict())

# copy task instances to new user
# for x in ['questionTaskInstances', 'foodTaskInstances', 'placeTaskInstances', 'trashBinTaskInstances']:
#      taskInstances = db.collection('users').document('156992599').collection(x).get()
#      taskInstancesRef = db.collection('users').document('641517503').collection(x)
#      for instance in taskInstances:
#          taskInstancesRef.add(instance.to_dict())

# task template create-place
createPlaceTemplate = db.collection('taskTemplates').document('create-place').get().to_dict()
questionsCreatePlace = createPlaceTemplate['questions']
taskTemplates = db.collection('taskTemplates').get()

for task in taskTemplates:
    questions = task.to_dict()['questions']
    questions.insert(len(questions), questionsCreatePlace[-1])
    db.collection('taskTemplates').document(task.id).update({'questions': questions})
