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

excludeUsers = ['i.p.samiotis@tudelft.nl', 's.qiu-1@tudelft.nl', 'nehasreet@gmail.com', 'nehasreenishi@gmail.com', 'enreina@gmail.com', '641517503', '20791653', '178336114', '271561032', '874886396', '555780883', '444883337', '827717938', '156992599']

getUsers = db.collection('users').get()
allUsers = [x for x in getUsers]
chatbotv1Users = []
chatbotv2Users = []
mobileAppUsers = []

activeUsers = 0
for user in allUsers:
    userData = user.to_dict()
    numTasksCompleted = len(userData.get('tasksCompleted', []))
    if userData.get('telegramId', False) and userData['telegramId'] not in excludeUsers:
        if userData.get('chatbotv2', False):
            chatbotv2Users.append(userData)
            if (numTasksCompleted > 2):
                activeUsers = activeUsers + 1
        else:
            chatbotv1Users.append(userData)
    elif userData.get('email', False) and userData['email'] not in excludeUsers:
        mobileAppUsers.append(userData)
        # if (numTasksCompleted > 1):
        #     activeUsers = activeUsers + 1

    

print([x['telegramId'] for x in chatbotv1Users])
print(len(chatbotv1Users))
print([x['telegramId'] for x in chatbotv2Users])
print(len(chatbotv2Users))
print(len(mobileAppUsers))
print(activeUsers)


