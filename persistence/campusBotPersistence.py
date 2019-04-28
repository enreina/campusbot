from telegram.ext import BasePersistence
import db.firestoreClient as FirestoreClient
from collections import defaultdict
from pprint import pprint

class CampusBotPersistence(BasePersistence):

    def __init__(self, store_user_data=True, store_chat_data=True):
        self.store_user_data = store_user_data
        self.store_chat_data = store_chat_data
    
    def update_chat_data(self, chat_id, data):
        FirestoreClient.createDocument('botChatData', documentId=str(chat_id), data=data, merge=False)
    
    def update_user_data(self, user_id, data):
        FirestoreClient.createDocument('botUserData', documentId=str(user_id), data=data, merge=False)

    def update_conversation(self, name, key, new_state):
        FirestoreClient.createDocument('botConversations', documentId=str(name), data={str(key[0]):{str(key[1]): new_state}}, merge=True)

    def get_chat_data(self):
        chat_data = FirestoreClient.getCollection('botChatData', asDict=True)
        if chat_data is None:
            return defaultdict(dict)
        else:
            returnChatData = {}
            for chatId in chat_data:
                returnChatData[int(chatId)] = chat_data[chatId]
            return defaultdict(dict, returnChatData)

    def get_user_data(self):
        user_data = FirestoreClient.getCollection('botUserData', asDict=True)
        if user_data is None:
            return defaultdict(dict)
        else:
            returnUserData = {}
            for userId in user_data:
                returnUserData[int(userId)] = user_data[userId]
            return defaultdict(dict, returnUserData)
        return defaultdict(dict, user_data)

    def get_conversations(self, name):
        conversations = FirestoreClient.getDocument('botConversations', name)
        if conversations is None:
            return {}
        else:
            conversations_dict = {}
            for key1 in conversations:
                if isinstance(conversations[key1], dict):
                    for key2 in conversations[key1]:
                        conversations_dict[(int(key1), int(key2))] = conversations[key1][key2]
            pprint(conversations_dict)
            return conversations_dict

    def flush(self):
        return



    
