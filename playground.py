import db.firestoreClient as FirestoreClient
import datetime
from google.cloud import firestore

# print(FirestoreClient.getDocument('tasks', 'create-place', populate=False))

# taskExecutioner = TaskExecutioner('create-place')
# taskExecutioner.startTask()


# dummy places
newItem = FirestoreClient.createDocument('placeItems', documentId='9Uo69a5XgwaXdPejQupG', data={})
newTask = FirestoreClient.createDocument('placeTasks', data={
    'itemId': unicode(newItem.get().id),
    'item': newItem,
    'type': 0,
    'createdAt': firestore.SERVER_TIMESTAMP
})
user = FirestoreClient.getDocument('users', '156992599', withRef=True)
newTaskInstance = FirestoreClient.createDocument('placeTaskInstances', data={
    'taskId': unicode(newTask.get().id),
    'task': newTask,
    'userId': unicode(user['_id']),
    'user': user['_ref'],
    'createdAt': firestore.SERVER_TIMESTAMP
})

