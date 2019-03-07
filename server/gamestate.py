from block import Block
class gamestate:
    board = [[]]
    def __init__(self):
        #create board and 
        self.board = [[Block.STABLE for i in range(10)]for j in range(10)]
    
    def check_block(self,i,j):
        return self.board[i][j]
    
    def change_block(self,i,j):
        if self.board[i][j] is not Block.HOLE:
            self.board[i][j] += 1
            
 
        

    


