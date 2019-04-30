import datetime
import firestoreClient as FirestoreClient
from google.cloud import firestore

class User(object):

    @staticmethod
    def getUserById(userId):
        user = FirestoreClient.getDocument('users', userId, withRef=True)
        if user is None:
            return User.createANewUser(userId)
        else:
            return user

    @staticmethod
    def createANewUser(telegramId):
        newUser = {
            'telegramId': telegramId,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'tasksCompleted': [],
            'totalTasksCompleted': {'place': 0, 'question': 0, 'food': 0, 'trashbin': 0}
        }
        FirestoreClient.createDocument('users', documentId=telegramId, data=newUser)

        return FirestoreClient.getDocument('users', telegramId, withRef=True)

    @staticmethod
    def updateUser(userId, data):
        return FirestoreClient.updateDocument('users', userId, data)

    @staticmethod
    def saveUtterance(telegramId, message, byBot=False, callbackQuery=None):
        utteranceCollection = FirestoreClient.db.collection('users').document(str(telegramId)).collection('utterances')
        messageData = {
            'createdAt': message.date,
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