import db.firestoreClient as FirestoreClient
import datetime
from dateutil.tz import tzlocal
from google.cloud import firestore
from db.taskTemplate import TaskTemplate
import json
from pprint import pprint
from google.cloud.firestore_v1beta1.document import DocumentReference
from db.firestoreClient import db

# user conversion count
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

print("Mobile App")
print("#Users: {count}".format(
    count=len(mobileAppUsers)
))    
print("#Users who completed at least 1 task: {count}".format(
    count=len([x for x in mobileAppUsers if len(x.get('tasksCompleted',[])) >= 1])
))   
print("#Users who completed at least 2 task: {count}".format(
    count=len([x for x in mobileAppUsers if len(x.get('tasksCompleted',[])) >= 2])
)) 
print("#Users who completed at least 3 task: {count}".format(
    count=len([x for x in mobileAppUsers if len(x.get('tasksCompleted',[])) >= 3])
))     

print("Chatbot 1")
print("#Users of Chatbot 1: {count}".format(
    count=len(chatbotv1Users)
))
print("#Users who completed at least 1 task: {count}".format(
    count=len([x for x in chatbotv1Users if len(x.get('tasksCompleted',[])) >= 1])
))  
print("#Users who completed at least 2 task: {count}".format(
    count=len([x for x in chatbotv1Users if len(x.get('tasksCompleted',[])) >= 2])
)) 
print("#Users who completed at least 3 task: {count}".format(
    count=len([x for x in chatbotv1Users if len(x.get('tasksCompleted',[])) >= 3])
))   

print("Chatbot 2")
print("#Users of Chatbot 2: {count}".format(
    count=len(chatbotv2Users)
))
print("#Users who completed at least 1 task: {count}".format(
    count=len([x for x in chatbotv2Users if len(x.get('tasksCompleted',[])) >= 1])
))  
print("#Users who completed at least 2 task: {count}".format(
    count=len([x for x in chatbotv2Users if len(x.get('tasksCompleted',[])) >= 2])
)) 
print("#Users who completed at least 3 task: {count}".format(
    count=len([x for x in chatbotv2Users if len(x.get('tasksCompleted',[])) >= 3])
))  

# executed time
print("ChatbotVersion\titemId\ttaskType\tuserId\tcreatedAt\texecutionTime")
rowTemplate = "{chatbotVersion}\t{itemId}\t{taskType}\t{userId}\t{createdAt}\t{executionTime}"
# only consider from this date
startTime = datetime.datetime(2019,5,16,tzinfo=tzlocal())
# place items

getPlaceItems = db.collection('placeItems').get()
allPlaceItems = [(x.id, x.to_dict()) for x in getPlaceItems]
chatbot1TelegramIds = [x['telegramId'] for x in chatbotv1Users]
chatbot2TelegramIds = [x['telegramId'] for x in chatbotv2Users]

for placeItemId, placeItem in allPlaceItems:
    authorId = placeItem.get('authorId', None)
    executionTime = (placeItem['createdAt'] - placeItem['executionStartTime']).total_seconds()
    if authorId in chatbot1TelegramIds and 'executionStartTime' in placeItem:
        chatbotVersion = "Chatbot 1"
    elif authorId in chatbot2TelegramIds and 'executionStartTime' in placeItem:
        chatbotVersion = "Chatbot 2"
    else:
        continue

    print(rowTemplate.format(
        chatbotVersion=chatbotVersion,
        itemId=placeItemId,
        taskType="create",
        userId=authorId,
        createdAt=placeItem['createdAt'],
        executionTime=executionTime
    ))

# place enrichments
getPlaceEnrichments = db.collection('placeEnrichments').get()
allPlaceEnrichments = [x.to_dict() for x in getPlaceEnrichments]
chatbot1TelegramIds = [x['telegramId'] for x in chatbotv1Users]
chatbot2TelegramIds = [x['telegramId'] for x in chatbotv2Users]

for placeEnrichment in allPlaceEnrichments:
    authorId = placeEnrichment['taskInstance'].parent.parent.id
    if 'executionStartTime' not in placeEnrichment:
        continue
    executionTime = (placeEnrichment['createdAt'] - placeEnrichment['executionStartTime']).total_seconds()
    try:
        placeItemId = placeEnrichment['taskInstance'].get().get('task').get().get('itemId')
    except:
        continue
    if authorId in chatbot1TelegramIds and 'executionStartTime' in placeEnrichment:
        chatbotVersion = "Chatbot 1"
    elif authorId in chatbot2TelegramIds and 'executionStartTime' in placeEnrichment:
        chatbotVersion = "Chatbot 2"
    else:
        continue

    print(rowTemplate.format(
        chatbotVersion=chatbotVersion,
        itemId=placeItemId,
        taskType="enrich",
        userId=authorId,
        createdAt=placeEnrichment['createdAt'],
        executionTime=executionTime
    ))

# place validations


