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
        userData['id'] = user.id
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

def summary_execution_time(domain="place"):
    # executed time
    print("ChatbotVersion\titemId\tenrichmentId\tvalidationId\ttaskType\tuserId\tcreatedAt\texecutionTime")
    rowTemplate = "{chatbotVersion}\t{itemId}\t{enrichmentId}\t{validationId}\t{taskType}\t{userId}\t{createdAt}\t{executionTime}"
    # place items

    getPlaceItems = db.collection(domain + 'Items').get()
    allPlaceItems = [(x.id, x.to_dict()) for x in getPlaceItems]
    chatbot1TelegramIds = [x['telegramId'] for x in chatbotv1Users]
    chatbot2TelegramIds = [x['telegramId'] for x in chatbotv2Users]
    mobileAppIds = [x["id"] for x in mobileAppUsers]

    for placeItemId, placeItem in allPlaceItems:
        authorId = placeItem.get('authorId', None)
        if 'executionStartTime' not in placeItem:
            executionTime = None
        else:
            executionTime = (placeItem['createdAt'] - placeItem['executionStartTime']).total_seconds()
        
        if authorId in chatbot1TelegramIds:
            chatbotVersion = "Chatbot 1"
        elif authorId in chatbot2TelegramIds:
            chatbotVersion = "Chatbot 2"
        elif authorId in mobileAppIds:
            chatbotVersion = "Mobile App" 
        else:
            continue

        print(rowTemplate.format(
            chatbotVersion=chatbotVersion,
            itemId=placeItemId,
            enrichmentId=None,
            validationId=None,
            taskType="create",
            userId=authorId,
            createdAt=placeItem['createdAt'],
            executionTime=executionTime
        ))

    # place enrichments
    getPlaceEnrichments = db.collection(domain + 'Enrichments').get()
    allPlaceEnrichments = [(x.id, x.to_dict()) for x in getPlaceEnrichments]
    chatbot1TelegramIds = [x['telegramId'] for x in chatbotv1Users]
    chatbot2TelegramIds = [x['telegramId'] for x in chatbotv2Users]

    for enrichmentId, placeEnrichment in allPlaceEnrichments:
        try: 
            authorId = placeEnrichment['taskInstance'].parent.parent.id
            if 'executionStartTime' not in placeEnrichment:
                executionTime = None
            else:
                executionTime = (placeEnrichment['createdAt'] - placeEnrichment['executionStartTime']).total_seconds()
            
            try:
                placeItemId = placeEnrichment['taskInstance'].get().get('task').get().get('itemId')
            except:
                placeItemId = None

            if authorId in chatbot1TelegramIds:
                chatbotVersion = "Chatbot 1"
            elif authorId in chatbot2TelegramIds:
                chatbotVersion = "Chatbot 2"
            elif authorId in mobileAppIds:
                chatbotVersion = "Mobile App" 
            else:
                continue

            print(rowTemplate.format(
                chatbotVersion=chatbotVersion,
                itemId=placeItemId,
                enrichmentId=enrichmentId,
                validationId=None,
                taskType="enrich",
                userId=authorId,
                createdAt=placeEnrichment['createdAt'],
                executionTime=executionTime
            ))
        except:
            continue

    # place validations
    getPlaceValidations = db.collection(domain + 'Validations').get()
    allPlaceValidations = [(x.id, x.to_dict()) for x in getPlaceValidations]
    chatbot1TelegramIds = [x['telegramId'] for x in chatbotv1Users]
    chatbot2TelegramIds = [x['telegramId'] for x in chatbotv2Users]

    for validationId,placeValidation in allPlaceValidations:
        try:
            authorId = placeValidation['taskInstance'].parent.parent.id
            if 'executionStartTime' not in placeValidation:
                executionTime = None
            else:
                executionTime = (placeValidation['createdAt'] - placeValidation['executionStartTime']).total_seconds()
                try:
                    placeItemId = placeValidation['taskInstance'].get().get('task').get().get('itemId')
                except:
                    placeItemId = None

            if authorId in chatbot1TelegramIds:
                chatbotVersion = "Chatbot 1"
            elif authorId in chatbot2TelegramIds:
                chatbotVersion = "Chatbot 2"
            elif authorId in mobileAppIds:
                chatbotVersion = "Mobile App" 
            else:
                continue

            print(rowTemplate.format(
                chatbotVersion=chatbotVersion,
                itemId=placeItemId,
                enrichmentId=None,
                validationId=validationId,
                taskType="validate",
                userId=authorId,
                createdAt=placeValidation['createdAt'],
                executionTime=executionTime
            ))
        except:
            continue

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
        skipUtterances = db.collection('users').document(user['telegramId']).collection('utterances').where(u'text', u'==', u'/skip').get()
        skipCount = len([utter for utter in skipUtterances])
        userUtterances = db.collection('users').document(user['telegramId']).collection('utterances').where(u'byBot', u'==', False).get()
        utterCount = len([utter for utter in userUtterances])

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

        
        print("{telegramId}\t{registeredAt}\t{createCount}\t{enrichCount}\t{validateCount}\t{totalTaskCount}\t{skipCount}\t{utterCount}".format(
            telegramId=user['telegramId'],
            registeredAt=user['createdAt'].strftime("%Y-%m-%d %H:%M:%S"),
            createCount=totalCountCreate,
            enrichCount=totalCountEnrich,
            validateCount=totalCountValidate,
            totalTaskCount=totalCountCreate+totalCountEnrich+totalCountValidate,
            skipCount=skipCount,
            utterCount=utterCount
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
        
def fix_image_url():
    for domain in ['place', 'trashBin', 'question', 'food']:
        items = db.collection(domain + 'Items').get()

        for item in items:
            itemDict = item.to_dict()
            if 'imageUrl' in itemDict and itemDict['imageUrl'] is not None:
                imageUrl = itemDict['imageUrl']
                print(imageUrl)
                imageUrl = imageUrl.replace('http://campusbot.cf', 'https://hcbot.cf')
                imageUrl = imageUrl.replace('https://campusbot.cf', 'https://hcbot.cf')
                print(imageUrl)
                db.collection(domain + 'Items').document(item.id).update({'imageUrl': imageUrl})

def move_image_to_firebase_storage():
    for domain in ['place', 'trashBin', 'question', 'food']:
        items = db.collection(domain + 'Items').get()

        for item in items:
            itemDict = item.to_dict()
            imageTelegramFileId = itemDict.get('imageTelegramFileId', None)
            if imageTelegramFileId is not None:
                imageUrl = u"https://firebasestorage.googleapis.com/v0/b/campusbot-b7b7f.appspot.com/o/campusbot%2F{imageTelegramFileId}.jpg?alt=media&token=27af2a94-be62-456c-b9c2-1b3efa2c465b".format(
                    imageTelegramFileId=imageTelegramFileId
                )
                db.collection(domain + 'Items').document(item.id).update({'imageUrl': imageUrl})

def count_skip():
    for user in chatbotv1Users + chatbotv2Users:
        skipUtterances = db.collection('users').document(user['telegramId']).collection('utterances').where(u'text', u'==', u'/skip').get()
        skipCount = len([utter for utter in skipUtterances])

        print("{telegramId}\t{skipCount}".format(
            telegramId=user['telegramId'],
            skipCount=skipCount
        ))

def print_answers_create(domain="place"):
    if domain == "place":
        propertyKeys = ["imageUrl", "name", "categoryName", "geolocation", "buildingName", "floorNumber", "route", "hasElectricityOutlet", "seatCapacity"]
    elif domain == "food":
        propertyKeys = ["imageUrl", "name", "price", "geolocation", "foodLocation"]
    
    # header
    print("ChatbotVersion\titemId\ttaskType\tuserId\tcreatedAt\t{propertyKeys}".format(propertyKeys="\t".join(propertyKeys)))
    rowTemplate = "{chatbotVersion}\t{itemId}\t{taskType}\t{userId}\t{createdAt}\t" + ("\t".join(["{answer["+propKey+"]}" for propKey in propertyKeys]))
    
    # place items
    getPlaceItems = db.collection(domain + 'Items').get()
    allPlaceItems = [(x.id, x.to_dict()) for x in getPlaceItems]
    chatbot1TelegramIds = [x['telegramId'] for x in chatbotv1Users]
    chatbot2TelegramIds = [x['telegramId'] for x in chatbotv2Users]

    for placeItemId, placeItem in allPlaceItems:
        authorId = placeItem.get('authorId', None)
        if authorId in chatbot1TelegramIds and 'executionStartTime' in placeItem:
            chatbotVersion = "Chatbot 1"
        elif authorId in chatbot2TelegramIds and 'executionStartTime' in placeItem:
            chatbotVersion = "Chatbot 2"
        else:
            continue

        answer = {}
        for key in propertyKeys:
            answer[key] = placeItem.get(key, None)

        print(rowTemplate.format(
            chatbotVersion=chatbotVersion,
            itemId=placeItemId,
            taskType="create",
            userId=authorId,
            createdAt=placeItem['createdAt'],
            answer=answer
        ))

def print_answers_enrich(domain="place"):
    if domain == 'place':
        propertyKeys = ["imageUrl", "name", "categoryName", "geolocation", "buildingName", "floorNumber", "route", "hasElectricityOutlet", "seatCapacity"]
    elif domain == "food":
        propertyKeys = ["imageUrl", "mealCategory", "priceOpinion"]
        
    # header
    print("ChatbotVersion\titemId\ttaskType\tuserId\tcreatedAt\t{propertyKeys}".format(propertyKeys="\t".join(propertyKeys)))
    rowTemplate = "{chatbotVersion}\t{itemId}\t{taskType}\t{userId}\t{createdAt}\t" + ("\t".join(["{answer["+propKey+"]}" for propKey in propertyKeys]))
    # place enrichments
    getPlaceEnrichments = db.collection(domain + 'Enrichments').get()
    allPlaceEnrichments = [x.to_dict() for x in getPlaceEnrichments]
    chatbot1TelegramIds = [x['telegramId'] for x in chatbotv1Users]
    chatbot2TelegramIds = [x['telegramId'] for x in chatbotv2Users]

    for placeEnrichment in allPlaceEnrichments:
        answer = {}
        try:
            authorId = placeEnrichment['taskInstance'].parent.parent.id
            placeItemId = placeEnrichment['taskInstance'].get().get('task').get().get('itemId')
        except:
            continue
        if authorId in chatbot1TelegramIds:
            chatbotVersion = "Chatbot 1"
        elif authorId in chatbot2TelegramIds:
            chatbotVersion = "Chatbot 2"
        else:
            continue

        for key in propertyKeys:
            answer[key] = placeEnrichment.get(key, None)

        placeItem = db.collection(domain + 'Items').document(placeItemId).get()
        placeItemData = placeItem.to_dict()
        answer['imageUrl'] = placeItemData.get('imageUrl', None)
        if domain == "place":
            answer['name'] = placeItemData.get('name', None)
            answer['categoryName'] = placeItemData.get('categoryName', None)
            answer['geolocation'] = placeItemData.get('geolocation', None)

        print(rowTemplate.format(
            chatbotVersion=chatbotVersion,
            itemId=placeItemId,
            taskType="enrich",
            userId=authorId,
            createdAt=placeEnrichment['createdAt'],
            answer=answer
        ))

def print_answers_validate(domain="place"):
    if domain == 'place':
        propertyKeys = [
            "imageUrl", "name", "categoryName", "geolocation", 
            "buildingName", "floorNumber", "route", "seatCapacity",
            "isPlace", "isCategoryValid", "isBuildingValid", "isFloorNumberValid", "isBuildingNumberValid", "isRouteValid", "hasElectricityOutlet", "isSeatCapacityValid"]
    elif domain == 'food':
        propertyKeys = [
            "imageUrl", "isFoodPicture", "mealCategoryCheck"
        ]
    # header
    print("ChatbotVersion\titemId\ttaskType\tuserId\tcreatedAt\t{propertyKeys}".format(propertyKeys="\t".join(propertyKeys)))
    rowTemplate = "{chatbotVersion}\t{itemId}\t{taskType}\t{userId}\t{createdAt}\t" + ("\t".join(["{answer["+propKey+"]}" for propKey in propertyKeys]))
    # place validations
    getPlaceValidations = db.collection(domain + 'Validations').get()
    allPlaceValidations = [x.to_dict() for x in getPlaceValidations]
    chatbot1TelegramIds = [x['telegramId'] for x in chatbotv1Users]
    chatbot2TelegramIds = [x['telegramId'] for x in chatbotv2Users]

    for placeValidation in allPlaceValidations:
        answer = {}
        try:
            authorId = placeValidation['taskInstance'].parent.parent.id
            placeTask = placeValidation['taskInstance'].get().get('task').get()
            placeItemId = placeTask.get('itemId')
        except:
            continue
        if authorId in chatbot1TelegramIds:
            chatbotVersion = "Chatbot 1"
        elif authorId in chatbot2TelegramIds:
            chatbotVersion = "Chatbot 2"
        else:
            continue


        placeAggregation = placeTask.to_dict().get("aggregatedAnswers", {})
        for key in propertyKeys:
            answer[key] = placeAggregation.get(key, placeValidation.get(key, None))

        print(rowTemplate.format(
            chatbotVersion=chatbotVersion,
            itemId=placeItemId,
            taskType="validate",
            userId=authorId,
            createdAt=placeValidation['createdAt'],
            answer=answer
        ))

summary_execution_time(domain="trashBin")