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
            'tasksCompleted': [],
            'totalTasksCompleted': {'place': 0, 'course': 0, 'food': 0, 'trashbin': 0}
        }
        FirestoreClient.createDocument('users', documentId=telegramId, data=newUser)

        return FirestoreClient.getDocument('users', telegramId, withRef=True)

    