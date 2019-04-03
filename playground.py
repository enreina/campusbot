import db.firestoreClient as FirestoreClient
import datetime

# print(FirestoreClient.getDocument('tasks', 'create-place', populate=False))

# taskExecutioner = TaskExecutioner('create-place')
# taskExecutioner.startTask()


# dummy places
# FirestoreClient.createDocument('placeItems', {
#     'image': u'https://d1rkab7tlqy5f1.cloudfront.net/_processed_/3/a/csm_bieb_zon_1_4900798827_o_c8d2b550e5.jpg',
# 	'name': u'TU Delft Library',
# 	'geolocation': { 
# 		'latitude': 52.0027092, 
# 		'longitude': 4.3731207
# 	},
# 	'category': u'Building',
#     'buildingNumber': 21,
# 	'route': u'Prometheusplein 1, 2628 ZC Delft',
# 	'electricityOutlet': True
# })

FirestoreClient.createDocument('placeTasks', {
    'itemId': u'9Uo69a5XgwaXdPejQupG',
    'type': 0,
    'createdAt': datetime.datetime.now()
})

