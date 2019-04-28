from telegram.ext import BasePersistence
import db.firestoreClient as FirestoreClient
from collections import defaultdict
from pprint import pprint

class CampusBotPersistence(BasePersistence):

    def __init__(self, store_user_data=True, store_chat_data=True):
        self.store_user_data = store_user_data
        self.store_chat_data = store_chat_data
    
    def update_chat_data(self, chat_id, data):
        FirestoreClient.createDocument('botChatData', documentId=str(chat_id), data=data)
    
    def update_user_data(self, user_id, data):
        FirestoreClient.createDocument('botUserData', documentId=str(user_id), data=data)

    def update_conversation(self, name, key, new_state):
        FirestoreClient.createDocument('botConversations', documentId=str(name), data={str(key[0]):{str(key[1]): new_state}}, merge=True)

    def get_chat_data(self):
        chat_data = FirestoreClient.getCollection('botChatData', asDict=True)
        if chat_data is None:
            return defaultdict(dict)
        return defaultdict(dict, chat_data)

    def get_user_data(self):
        user_data = FirestoreClient.getCollection('botUserData', asDict=True)
        if user_data is None:
            return defaultdict(dict)
        return defaultdict(dict, user_data)

    def get_conversations(self, name):
        conversations = FirestoreClient.getDocument('botConversations', name)
        if conversations is None:
            return {}
        else:
            conversations_dict = {}
            for name in conversations:
                for key1, key2_state in conversations[name].items():
                    for key2 in key2_state:
                        conversations_dict[(key1, key2)] = key2_state[key2]
            return conversations_dict

    def flush(self):
        return



    
