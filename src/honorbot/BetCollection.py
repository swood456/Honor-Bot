import pymongo

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

    def getAllOpenBets(self):
        self.collection.find({ 'state': 'Open' })