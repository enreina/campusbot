import db.firestoreClient as FirestoreClient

print(FirestoreClient.getDocument('tasks', 'create-place', populate=True))