from db.firestoreClient import FirestoreClient
import settings as env

firestoreClient = FirestoreClient(env.FIRESTORE_SERVICE_ACCOUNT_PATH)

print(firestoreClient.getCollection('tasks', populate=True))