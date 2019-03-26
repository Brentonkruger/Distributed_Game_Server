# This class is for a player instance on the server
class Player:
    def __init__(self):
        self.power = 0
        self.movement = []
    
    def current_movement(self, movelist):
        self.movement = movelist

    def intended_movement(self):
        return self.movement
    
    def powerup(self, n_power_up):
        self.power += n_power_up

    def __lt__(self, other):
        return self.power < other.power
