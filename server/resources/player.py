
class Player:
    power = 0
    movement = []

    def __init__(self):
        self.power = 0
    
    def current_movement(self, movelist):
        self.movement = movelist
