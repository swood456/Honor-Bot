import pymongo

K_INITIAL_USER_HONOR = 100

class UserCollection:
    def __init__(self, database):
        self.collection = database.users
    
    def user_exists(self, user_id):
        return self.collection.count_documents({ '_id': user_id }) != 0

    def find_user(self, user_id):
        return self.collection.find_one({ '_id': user_id })

    def add_user(self, user_id):
        self.collection.insert_one({
            "_id": user_id,
            "honor": K_INITIAL_USER_HONOR
        })
    # def find_next_display_id(self):
    #     max_display_id_document = self.collection.find_one(sort=[("display_id", pymongo.DESCENDING)])

    #     max_display_id = 0
    #     if max_display_id_document is not None:
    #         max_display_id = max_display_id_document.get('display_id', 0)
        
    #     return max_display_id + 1
    
    # def insert_bet(self, bet):
    #     self.collection.insert_one(bet.__dict__)

    # def find_all_open_bets(self):
    #     docs = self.collection.find({'state': 'Open'})
    #     result = []
    #     for doc in docs:
    #         result.append(HonorBet.create_from_json(doc))
    #     return result
    
    # def find_all_user_bets(self, user_id):
    #     query = {"$and":[{"$or":[ {"player1": user_id}, {"player2": user_id}]}, {'state': 'Open'}]}
    #     docs = self.collection.find(query)
    #     result = []
    #     for doc in docs:
    #         result.append(HonorBet.create_from_json(doc))
    #     return result

    # def find_by_display_id(self, display_id):
    #     return HonorBet.create_from_json(self.collection.find_one({'display_id': display_id}))