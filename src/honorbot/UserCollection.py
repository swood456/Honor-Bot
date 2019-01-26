import pymongo

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
        })
    
    def update_user(self, user):
        self.collection.update_one({'_id': user['_id']}, {'$set': user}, upsert=False)

    def get_all_users(self):
        return self.collection.find({})