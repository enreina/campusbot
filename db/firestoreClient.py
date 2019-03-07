
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1beta1.document import DocumentReference 
from google.cloud.firestore_v1beta1 import ArrayUnion
import settings as env
from bunch import Bunch

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
        documentDictionary = doc.to_dict()
        documentDictionary['_id'] = doc.id
        return documentDictionary
    except google.cloud.exceptions.NotFound:
        print(u'No such document!')

def saveDocument(collectionName, documentId=None, data={}, merge=True):
    db.collection(collectionName).document(documentId).set(data, merge=merge)

def updateDocument(collectionName, documentId, data):
    db.collection(collectionName).document(documentId).update(data)

def updateArrayInDocument(collectionName, documentId, arrayProperty, newArray):
    updateDocument(collectionName, documentId, {arrayProperty: ArrayUnion(newArray)})

def getDocuments(collectionName, queries=[]):
    collectionRef = db.collection(collectionName)
    for query in queries:
        collectionRef = collectionRef.where(query[0], query[1], query[2])
    collectedData = collectionRef.get()
    documentsAsList = []
    for item in collectedData:
        itemAsDict = item.to_dict()
        itemAsDict['_id'] = item.id
        documentsAsList.append(Bunch(itemAsDict))
   
    return documentsAsList
