from enum import Enum

class Block(Enum):
    STABLE = 0
    CRACKED = 1
    HOLE = 2
     
class Gamestate:
    board = [[]]
    def __init__(self):
        #create board and 
        self.board = [[Block.STABLE for i in range(10)]for j in range(10)]
    
    def check_block(self,i,j):
        return self.board[i][j]
    
    def change_block(self,i,j):
        if self.board[i][j] is Block.STABLE:
            self.board[i][j] = Block.CRACKED
        else:
            self.board[i][j] = Block.HOLE
 
        

    


