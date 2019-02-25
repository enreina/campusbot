import db.firestoreClient as FirestoreClient
from hc.taskExecutioner import TaskExecutioner

# print(FirestoreClient.getDocument('tasks', 'create-place', populate=True))

taskExecutioner = TaskExecutioner('create-place')
taskExecutioner.startTask()