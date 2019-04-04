#The logic for all gamestate code

from enum import Enum

class BlockState(Enum):
    STABLE = 0
    CRACKED = 1
    HOLE = 2

class Block():
    def __init__(self):
        self.has_powerup = False
        self.block_state = BlockState.STABLE

    def __repr__(self):
        if self.block_state == BlockState.STABLE:
            return "[S]"
        if self.block_state == BlockState.CRACKED:
            return "[C]"
        if self.block_state == BlockState.HOLE:
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
        self.board = [[Block() for x in range(size)] for y in range(size)]
        

    def print_board(self):
        string = ""
        for i in range(len(self.board)):
            for j in range(len(self.board)):
                string = string + repr(self.board[i][j]) 
            print(string + "\n")
            string = ""               
    
    def check_block_state(self,x,y):
        return self.board[x][y].block_state
    
    def check_block(self,x,y):
        return self.board[x][y]

    # Function used to change a block to the next state
    def change_block(self, x, y):
        if self.check_block_state(x, y) == BlockState.STABLE:
            self.stable_locations.remove((x,y))
            self.board[x][y].block_state = BlockState.CRACKED
            self.cracked_locations.add((x,y))
        elif self.check_block_state(x, y) == BlockState.CRACKED:
            self.cracked_locations.remove((x,y))
            self.board[x][y].block_state = BlockState.HOLE
            self.hole_locations.add((x,y))

    def add_powerup(self, x, y):
        if (self.board[x][y].has_powerup == True) or (self.check_block_state(x, y) == BlockState.HOLE):
            return False
        else:
            self.board[x][y].has_powerup = True
            return True

    def remove_powerup(self, x, y):
        self.board[x][y].has_powerup = False

    def transition_blocks(self):
        copy_of_cracked_locations = self.cracked_locations.copy()
        for tup in copy_of_cracked_locations:
            self.change_block(tup[0],tup[1])
            self.remove_powerup(tup[0],tup[1])

    def randomly_generate_powerups(self, quantity):
        return False

    def assign_players(self, number_of_players, board):
        return False

        

    


