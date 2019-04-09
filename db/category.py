import firestoreClient as FirestoreClient

class Category(object):

    @staticmethod
    def getSubcategories(itemCategory):
        return FirestoreClient.getDocuments('categories', [('subcategoryOf', '==', itemCategory)], withRef=True)

    @staticmethod
    def getCategoryById(categoryId):
        return FirestoreClient.getDocument('categories', categoryId, withRef=True)