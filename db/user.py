import firestoreClient as FirestoreClient

class User(object):
    @staticmethod
    def getUserById(id):
        return FirestoreClient.getDocument('users', id, withRef=True)

    