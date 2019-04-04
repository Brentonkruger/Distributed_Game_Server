#The logic for all gamestate code

from enum import Enum

class Block(Enum):
    STABLE = 0
    CRACKED = 1
    HOLE = 2
    
    def __init__(self, *args):
        self.has_powerup = False

    def __repr__(self):
        if self == Block.STABLE:
            return "[S]"
        if self == Block.CRACKED:
            return "[C]"
        if self == Block.HOLE:
            return "[H]"
     
class Board:

    stable_locations = set()
    cracked_locations = set()
    hole_locations = set()
    player_locations = set()
    powerup_locations = set()

    #Create a blank board, with a specified size (the width and height of the square board)
    def __init__(self, size):
        for i in range(size):
            for j in range(size):
                self.stable_locations.add((i,j))
                
        self.board = [[Block.STABLE]*size]*size

    def print_board(self):
        string = ""
        for i in range(len(self.board)):
            for j in range(len(self.board)):
                string = string + repr(self.board[i][j]) 
            print(string + "\n")
            string = ""               
    
    def check_block(self,x,y):
        return self.board[x][y]
    
    # Function used to change a block to the next state
    def change_block(self, x, y):
        if self.board[x][y] == Block.STABLE:
            self.stable_locations.remove((x,y))
            self.board[x][y] = Block.CRACKED
            self.cracked_locations.add((x,y))
        elif self.board[x][y] == Block.CRACKED:
            self.cracked_locations.remove((x,y))
            self.board[x][y] = Block.HOLE
            self.hole_locations.add((x,y))

    def add_powerup(self, x, y):
        if (self.board[x][y].has_powerup == True) or (self.board[x][y] == Block.HOLE):
            return False
        else:
            self.board[x][y].has_powerup = True
            return True

    def assign_players(number_of_players, board):
        return false

        

    


