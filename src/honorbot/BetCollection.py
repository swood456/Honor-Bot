import pymongo
from .HonorBet import HonorBet

class BetCollection:
    def __init__(self, database):
        self.collection = database.bets
    
    def find_next_display_id(self):
        max_display_id_document = self.collection.find_one(sort=[("display_id", pymongo.DESCENDING)])

        max_display_id = 0
        if max_display_id_document is not None:
            max_display_id = max_display_id_document.get('display_id', 0)
        
        return max_display_id + 1
    
    def insert_bet(self, bet):
        self.collection.insert_one(bet.__dict__)

    def find_all_open_bets(self):
        docs = self.collection.find({'state': HonorBet.open_state})
        result = []
        for doc in docs:
            result.append(HonorBet.create_from_json(doc))
        return result
    
    def find_all_user_bets(self, user_id):
        query = {"$and":[{"$or":[ {"player1": user_id}, {"player2": user_id}]}, {'state': HonorBet.open_state}]}
        docs = self.collection.find(query)
        result = []
        for doc in docs:
            result.append(HonorBet.create_from_json(doc))
        return result

    def find_by_display_id(self, display_id):
        document = self.collection.find_one({'display_id': display_id})
        if document is None: return None
        return HonorBet.create_from_json(document)

    def update_bet(self, bet):
        self.collection.update_one({'_id': bet._id}, {'$set': bet.__dict__}, upsert=False)