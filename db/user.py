import datetime
import firestoreClient as FirestoreClient
from google.cloud import firestore

class User(object):

    @staticmethod
    def getUserById(userId):
        try:
            return FirestoreClient.getDocument('users', userId, withRef=True)
        except:
            return User.createANewUser(userId)

    @staticmethod
    def createANewUser(telegramId):
        newUser = {
            'telegramId': telegramId,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'tasksCompleted': []
        }
        FirestoreClient.createDocument('users', documentId=telegramId, data=newUser)

        return FirestoreClient.getDocument('users', telegramId, withRef=True)

    