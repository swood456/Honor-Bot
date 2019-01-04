import datetime

class HonorBet:
    def __init__(self, player1, duration, message, display_id, id=None, player2=None, state="Open", date=datetime.datetime.now(), claimed_user=None, punishment_nickname=None):
        self.player1 = player1
        self.duration = duration
        self.message = message
        self.display_id = display_id
        self.player2 = player2
        self.state = state
        self.created_date = date
        self.claimed_user = claimed_user
        self.punishment_nickname = punishment_nickname
        if id is not None:
            self._id = id
    
    open_state = "Open"
    active_state = "Active"
    claimed_state = "Claimed"
    closed_state = "Completed"

    @classmethod
    def create_from_json(cls, bet_dict):
        return cls(bet_dict['player1'], bet_dict['duration'], bet_dict['message'], bet_dict['display_id'], bet_dict['_id'], bet_dict['player2'], bet_dict['state'], bet_dict['created_date'], bet_dict['claimed_user'], bet_dict['punishment_nickname'])