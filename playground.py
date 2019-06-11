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

def count_user_conversion():
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

def summary_execution_time():
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

def count_task_completed():
    print("userId\tfoodCount\tplaceCount\tcourseCount\ttrashBinCount")
    for user in chatbotv1Users + chatbotv2Users:
        print("{telegramId}\t{foodCount}\t{placeCount}\t{courseCount}\t{trashBinCount}".format(
            telegramId=user['telegramId'],
            foodCount=user.get('totalTasksCompleted', {}).get('food', 0),
            placeCount=user.get('totalTasksCompleted', {}).get('place', 0),
            courseCount=user.get('totalTasksCompleted', {}).get('question', 0),
            trashBinCount=user.get('totalTasksCompleted', {}).get('trashbin', 0)
        ))

def count_task_completed_by_type():
    for user in chatbotv1Users + chatbotv2Users:
        totalCountEnrich = 0
        totalCountValidate = 0
        totalCountCreate = 0
        for domain in ['food', 'place', 'question', 'trashBin']:
            totalTasksCompleted = user.get('totalTasksCompleted', {}).get(domain.lower(), 0)
            countEnrich = 0
            countValidate = 0
            # get task instances
            taskInstances = db.collection('users').document(user['telegramId']).collection(domain + 'TaskInstances').where(u'completed', u'==', True).get()
            
            for taskInstance in taskInstances:
                if taskInstance.to_dict()['task'].get().to_dict()['type'] == 0:
                    countEnrich = countEnrich + 1
                else:
                    countValidate = countValidate + 1

            countCreate = totalTasksCompleted - (countEnrich + countValidate)
            user['taskCompleted'] = {
                domain: {
                    'create': countCreate,
                    'enrich': countEnrich,
                    'validate': countValidate
                }
            }

            totalCountCreate = totalCountCreate + countCreate
            totalCountEnrich = totalCountEnrich + countEnrich
            totalCountValidate = totalCountValidate + countValidate

        
        print("{telegramId}\t{createCount}\t{enrichCount}\t{validateCount}".format(
            telegramId=user['telegramId'],
            createCount=totalCountCreate,
            enrichCount=totalCountEnrich,
            validateCount=totalCountValidate
        ))

def print_enrichment_detail():
    placeEnrichments = db.collection('placeEnrichments').get()

    print('placeEnrichmentId\titemId\tuserId\ttaskInstanceId')
    for placeEnrichment in placeEnrichments:
        placeEnrichmentId = placeEnrichment.id
        placeEnrichmentData = placeEnrichment.to_dict()
        userId = placeEnrichmentData['taskInstance'].parent.parent.id
        taskInstanceId = placeEnrichmentData['taskInstanceId']
        try:
            itemId = placeEnrichmentData['taskInstance'].get().to_dict()['task'].get().to_dict()['itemId']

            print("{placeEnrichmentId}\t{itemId}\t{userId}\t{taskInstanceId}".format(
                placeEnrichmentId=placeEnrichmentId,
                itemId=itemId,
                userId=userId,
                taskInstanceId=taskInstanceId    
            ))
        except:
            continue
        

print_enrichment_detail()


