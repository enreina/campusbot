import db.firestoreClient as FirestoreClient
from hc.taskExecutioner import TaskExecutioner

# print(FirestoreClient.getDocument('tasks', 'create-place', populate=False))

# taskExecutioner = TaskExecutioner('create-place')
# taskExecutioner.startTask()

# create-meal task
FirestoreClient.saveDocument('tasks', 'create-meal', 
    {   'openingStatement': u'Let\'s create a meal item',
        'closingStatement': u'Thank you \U0001f601! We have saved the information of this meal!',
        'entryCommand': u'food',
        'type': 0,
        'questions': 
        [
            {
                'text': u'Please upload a photo of the *meal* that you bought in campus',
                'property': u'image',
                'type': u'image',
                'responseOk': u'Nice photo!',
                'responseError': u'Please send me a photo of the meal using the camera or from your photo album by tapping the attachment (paper clip) icon',
                'confirmationText': u'This is the photo of *{item[name]}*',
            },
            {
                'text': u'What is the name of each food in the photo?\n\nYou can tell me multiple food separated with commas\nExample: fried egg, bread, milk',
                'property': u'name',
                'type': u'text',
                'responseOk': u'*{item[name]}*, huh? Looks delicious!',
                'responseError': u'Sorry, I couldn\'t quite get that'
            },
            {
                'text': u'How much did you pay for *{item[name]}*?',
                'property': u'price',
                'type': u'text',
                'responseOk': u'Good to know!',
                'responseError': u'Sorry, I couldn\'t quite get that',
                'confirmationText': 'The price of the meal is *{item[price]}*'
            },
            {
                'text': u'Where did you buy the meal?\n\nYou can send me your location or a custom location.',
                'property': u'location',
                'type': u'location',
                'responseOk': u'Good to know!',
                'responseError': u'Sorry, I couldn\'t quite get that',
                'confirmationText': 'This is where you bought the meal:'
            }
        ]
    })


