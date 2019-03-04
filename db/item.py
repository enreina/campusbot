import firestoreClient as FirestoreClient

class Item(object):

    @staticmethod
    def getItemsByType(itemType):
        return FirestoreClient.getDocuments('items', [('itemType', '==', itemType)])
    
