#The logic for all gamestate code

from enum import Enum

class Block(Enum):
    STABLE = 0
    CRACKED = 1
    HOLE = 2
    
    def __init__(self):
        self.has_powerup = False
     
class Board:
        #Create a stable board, with a specified size
    def __init__(self, length, width):
        self.board = [[Block.STABLE for i in range(width)]for j in range(length)]
    
    def check_block(self,x,y):
        return self.board[x][y]
    
    def change_block(self,x,y):
        if self.board[x][y] is Block.STABLE:
            self.board[x][y] = Block.CRACKED
        else:
            self.board[x][y] = Block.HOLE

    def add_powerup(self, x, y):
        # Invalid Powerup States
        if (self.board[x][y].has_powerup == True) or (not self.board[x][y] == Block.STABLE):
            return False
        else:
            self.board[x][y].has_powerup = True
            return True

        

    


