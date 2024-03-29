import datetime
import firestoreClient as FirestoreClient
from google.cloud import firestore
import common.campusbotApi as CampusBotApi
from dateutil.tz import tzlocal

class User(object):

    @staticmethod
    def getUserById(userId, userDetails={}):
        user = FirestoreClient.getDocument('users', userId, withRef=True)
        if user is None:
            return User.createANewUser(userId, userDetails)
        else:
            return user

    @staticmethod
    def createANewUser(telegramId, userDetails={}):
        newUser = {
            'telegramId': telegramId,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'tasksCompleted': [],
            'totalTasksCompleted': {'place': 0, 'question': 0, 'food': 0, 'trashbin': 0},
            'preferredLocationNames': [],
            'preferredCourses': [],
        }
        newUser.update(userDetails)
        FirestoreClient.createDocument('users', documentId=telegramId, data=newUser)

        # assign task to new user
        CampusBotApi.assign_task_to_user('place', telegramId)
        CampusBotApi.assign_task_to_user('question', telegramId)
        CampusBotApi.assign_task_to_user('food', telegramId)
        CampusBotApi.assign_task_to_user('trashbin', telegramId)

        return FirestoreClient.getDocument('users', telegramId, withRef=True)

    @staticmethod
    def updateUser(userId, data):
        return FirestoreClient.updateDocument('users', userId, data)

    @staticmethod
    def updatePreferredLocationNames(userId, locationName):
        return FirestoreClient.updateArrayInDocument('users', userId, 'preferredLocationNames', [locationName])

    @staticmethod
    def updatePreferredCourses(userId, course):
        return FirestoreClient.updateArrayInDocument('users', userId, 'preferredCourses', [course])

    @staticmethod
    def saveUtterance(telegramId, message, byBot=False, callbackQuery=None):
        utteranceCollection = FirestoreClient.db.collection('users').document(str(telegramId)).collection('utterances')
        messageData = {
            'createdAt': message.date.replace(tzinfo=tzlocal()),
            'byBot': byBot
        }
        if message.text:
            messageData['text']= message.text
        if message.photo:
            messageData['photo'] = [unicode(photo.file_id) for photo in message.photo]
        if message.location:
            messageData['location'] = {'latitude': message.location.latitude, 'longitude': message.location.longitude}
        if message.caption:
            messageData['caption'] = message.caption
        if callbackQuery is not None:
            messageData['data'] = callbackQuery.data

        utteranceCollection.document(str(message.message_id)).set(messageData)