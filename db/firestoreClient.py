
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1beta1.document import DocumentReference
class FirestoreClient(object):
    '''Main module to connect to firestore

    Attributes:
        db: the firestore clienc
    '''
    
    def __init__(self, serviceAccountPath):
        cred = credentials.Certificate(serviceAccountPath)
        firebase_admin.initialize_app(cred)

        self.db = firestore.client()

    def getCollection(self, collectionName, populate=False):
        ref = self.db.collection(collectionName)
        collectedData = ref.get()
        documentsAsList = [x.to_dict() for x in collectedData]

        if populate:
            for doc in documentsAsList:
                for key,value in doc.items():
                    if isinstance(value, DocumentReference):
                        # populate reference
                        doc[key] = value.get().to_dict()

        return documentsAsList