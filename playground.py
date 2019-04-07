import db.firestoreClient as FirestoreClient
import datetime
from google.cloud import firestore

# print(FirestoreClient.getDocument('tasks', 'create-place', populate=False))

# taskExecutioner = TaskExecutioner('create-place')
# taskExecutioner.startTask()


# dummy places
newItem = FirestoreClient.createDocument('questionItems', data={
    'imageUrl': u'http://campusbot.cf/images/blank-white-image.png',
	'question': u'When is the deadline for Assignment A',
    'courseName': 'Software Architecture',
    'topAnswer': 'Sunday 28th May',
    'createdAt': firestore.SERVER_TIMESTAMP
})
newTask = FirestoreClient.createDocument('questionTasks', data={
    'itemId': unicode(newItem.get().id),
    'item': newItem,
    'type': 0,
    'createdAt': firestore.SERVER_TIMESTAMP
})
user = FirestoreClient.getDocument('users', '156992599', withRef=True)
newTaskInstance = FirestoreClient.createDocument('questionTaskInstances', data={
    'taskId': unicode(newTask.get().id),
    'task': newTask,
    'userId': unicode(user['_id']),
    'user': user['_ref'],
    'createdAt': firestore.SERVER_TIMESTAMP
})

