
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1beta1.document import DocumentReference
import settings as env

cred = credentials.Certificate(env.FIRESTORE_SERVICE_ACCOUNT_PATH)
firebase_admin.initialize_app(cred)
db = firestore.client()

def getCollection(collectionName, populate=False):
    ref = db.collection(collectionName)
    collectedData = ref.get()
    documentsAsList = [x.to_dict() for x in collectedData]

    if populate:
        for doc in documentsAsList:
            for key,value in doc.items():
                if isinstance(value, DocumentReference):
                    # populate reference
                    doc[key] = value.get().to_dict()

    return documentsAsList

def getDocument(collectionName, documentId, populate=False):
    doc_ref = db.collection(collectionName).document(documentId)

    try:
        doc = doc_ref.get()
        return doc.to_dict()
    except google.cloud.exceptions.NotFound:
        print(u'No such document!')