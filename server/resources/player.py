# This class is for a player instance on the server
class Player:
    def __init__(self, id):
        self.power = 0
        self.movement = []
        self.id = id
        # Unassigned value of the player
        self.current_location = (-1, -1)
    
    def current_movement(self, movelist):
        self.movement = movelist

    def intended_movement(self):
        return self.movement
    
    def add_power(self, powerup_amount):
        self.power += powerup_amount

    def __lt__(self, other):
        return self.power < other.power
