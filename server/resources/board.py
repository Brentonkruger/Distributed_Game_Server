#The logic for all gamestate code

from enum import Enum

class Block(Enum):
    STABLE = 0
    CRACKED = 1
    HOLE = 2
     
class Board:
    board = [[]]
        #Create a stable board, with a specified size
    def __init__(self, length, width):
        self.board = [[Block.STABLE for i in range(length)]for j in range(width)]
    
    def check_block(self,i,j):
        return self.board[i][j]
    
    def change_block(self,i,j):
        if self.board[i][j] is Block.STABLE:
            self.board[i][j] = Block.CRACKED
        else:
            self.board[i][j] = Block.HOLE



    


