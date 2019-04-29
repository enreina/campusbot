
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1beta1.document import DocumentReference 
from google.cloud.firestore_v1beta1 import ArrayUnion
import settings as env
from bunch import Bunch
import google.cloud.exceptions

cred = credentials.Certificate(env.FIRESTORE_SERVICE_ACCOUNT_PATH)
firebase_admin.initialize_app(cred)
db = firestore.client()

def getCollection(collectionName, populate=False, asDict=False):
    ref = db.collection(collectionName)
    collectedData = ref.get()

    if asDict:
        documentsAsDict = {}
        for x in collectedData:
            documentsAsDict[x.id] = x.to_dict()
            if populate:
                doc = documentsAsDict[x.id]
                for key,value in doc.items():
                    if isinstance(value, DocumentReference):
                        # populate reference
                        doc[key] = value.get().to_dict()
        return documentsAsDict
    else:
        documentsAsList = [x.to_dict() for x in collectedData]
        if populate:
            for doc in documentsAsList:
                for key,value in doc.items():
                    if isinstance(value, DocumentReference):
                        # populate reference
                        doc[key] = value.get().to_dict()
        return documentsAsList


def getDocument(collectionName, documentId, populate=False, withRef=False):
    doc_ref = db.collection(collectionName).document(documentId)

    try:
        doc = doc_ref.get()
        documentDictionary = doc.to_dict()
        if documentDictionary is None:
            return
        documentDictionary['_id'] = doc.id
        if withRef:
            documentDictionary['_ref'] = doc_ref
        return documentDictionary
    except google.cloud.exceptions.NotFound:
        print(u'No such document!')
        return None

def createDocument(collectionName, documentId=None, data={}, merge=True):
    if documentId is not None:
        return saveDocument(collectionName, documentId=documentId, data=data, merge=merge)
    else:
        ref = db.collection(collectionName).document()
        ref.set(data, merge=merge)

        return ref

def saveDocument(collectionName, documentId=None, data={}, merge=True):
    ref = db.collection(collectionName).document(documentId)
    ref.set(data, merge=merge)

    return ref

def updateDocument(collectionName, documentId, data):
    db.collection(collectionName).document(documentId).update(data)

def updateArrayInDocument(collectionName, documentId, arrayProperty, newArray):
    updateDocument(collectionName, documentId, {arrayProperty: ArrayUnion(newArray)})

def getDocuments(collectionName=None, queries=[], withRef=False, populate=False, limit=None, orderBy=None, orderDirection=firestore.Query.ASCENDING, collectionRef=None):
    if collectionRef is None:
        collectionRef = db.collection(collectionName)
    originalCollectionRef = collectionRef

    for query in queries:
        collectionRef = collectionRef.where(query[0], query[1], query[2])
    if orderBy is not None:
        collectionRef = collectionRef.order_by(orderBy, direction=orderDirection)
    if limit is not None:
        collectionRef = collectionRef.limit(limit)
    collectedData = collectionRef.get()
    documentsAsList = []
    for item in collectedData:
        itemAsDict = item.to_dict()
        itemAsDict['_id'] = item.id
        if withRef:
            itemAsDict['_ref'] = originalCollectionRef.document(item.id)
        documentsAsList.append(Bunch(itemAsDict))
   
    return documentsAsList

def getDocumentsFromSubcollection(collectionName, documentId, subCollectionName, queries=[], withRef=False, populate=False, limit=None, orderBy=None, orderDirection=firestore.Query.ASCENDING):
    collectionRef = db.collection(collectionName).document(documentId).collection(subCollectionName)
    return getDocuments(queries=queries, withRef=withRef, populate=populate, limit=limit, orderBy=orderBy, orderDirection=orderDirection, collectionRef=collectionRef)

def getDocumentRef(collectionname, documentId):
    return db.collection(collectionname).document(documentId)
