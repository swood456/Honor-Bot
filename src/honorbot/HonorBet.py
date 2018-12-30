import datetime

class HonorBet:
    def __init__(self, player1, amount, message, display_id, id=None, player2=None, state="Open", date=datetime.datetime.now()):
        self.player1 = player1
        self.amount = amount
        self.message = message
        self.display_id = display_id
        self.player2 = player2
        self.state = state
        self.created_date = date
        if id is not None:
            self._id = id
    
    open_state = "Open"
    active_state = "Active"
    closed_state = "Closed"

    @classmethod
    def create_from_json(cls, bet_dict):
        return cls(bet_dict['player1'], bet_dict['amount'], bet_dict['message'], bet_dict['display_id'], bet_dict['_id'], bet_dict['player2'], bet_dict['state'], bet_dict['created_date'])