import firestoreClient as FirestoreClient

class Item(object):

    @staticmethod
    def getItemsByType(itemType):
        return FirestoreClient.getDocuments('items', [('itemType', '==', itemType)])

    @staticmethod
    def getSubtypes(itemType):
        return FirestoreClient.getDocuments('items', [('subclassOf', '==', itemType)], withRef=True)
    
    @staticmethod
    def getItemById(itemId, collectionName="items"):
        return FirestoreClient.getDocument(collectionName, itemId, withRef=True)
