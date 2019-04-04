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
    
    #Create a blank board, with a specified size (the width and height of the square board)
    def __init__(self, size):
        self.stable_locations = set()
        self.cracked_locations = set()
        self.hole_locations = set()
        self.player_locations = set()
        self.powerup_locations = set()
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

    def transition_blocks(self):
        copy_of_cracked_locations = self.cracked_locations.copy()
        for tup in copy_of_cracked_locations:
            self.change_block(tup[0],tup[1])

    def randomly_generate_powerups(self, quantity):
        return False

    def assign_players(self, number_of_players, board):
        return False

        

    


