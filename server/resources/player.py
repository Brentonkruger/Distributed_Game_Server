# This class is for a player instance on the server
class Player:
    power = 0
    movement = []

    def __init__(self):
        self.power = 0
    
    def current_movement(self, movelist):
        self.movement = movelist

    def intended_movement(self):
        return self.movement
        