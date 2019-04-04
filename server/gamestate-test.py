import unittest
from resources import board
from VR_replica import replica

class TestingBoard(unittest.TestCase):


    # Need numerous tests to get the game state proven to be working. 
    # 1. Create a board, with randomly assigned player locations, powerup locations, and an amount of "cracked" tiles
    # 2. Given some inputed movements, create a new valid gamestate


    def test_gamestate_regular_block_is_stable(self):
        # Initialize game size
        self.brd = board.Board(10)
        
        # Ensure that the two corners are both stable, and the stable_locations set is equal to 100
        self.assertEqual(self.brd.check_block(0,0), board.Block.STABLE)
        self.assertEqual(self.brd.check_block(9,9), board.Block.STABLE)
        self.assertEqual(len(self.brd.stable_locations), 100)

    def test_gamestate_complete_transition_of_block(self):
        # Initialize game size
        self.brd = board.Board(10)

        # Checking the inital gamestate initialization
        self.assertEqual(self.brd.check_block(2,2), board.Block.STABLE)
        self.assertTrue((2,2) in self.brd.stable_locations)

        # Checking the state after we do another change to cracked
        self.brd.change_block(2,2)
        self.assertEqual(self.brd.check_block(2,2), board.Block.CRACKED)
        self.assertFalse((2,2) in self.brd.stable_locations)
        self.assertEqual(self.brd.cracked_locations, {(2,2)})

        # Checking the state after we do the final change to hole
        self.brd.change_block(2,2)
        self.assertEqual(self.brd.check_block(2,2), board.Block.HOLE)
        self.assertFalse(self.brd.cracked_locations)
        self.assertEqual(self.brd.hole_locations, {(2,2)})

    def test_gamestate_powerup_addition_to_stable(self):
        # Initialize game size
        self.brd = board.Board(10)
        self.assertFalse(self.brd.check_block(1,1).has_powerup)
        self.brd.add_powerup(1,1)
        self.assertTrue(self.brd.check_block(1,1).has_powerup)
        

if __name__ == '__main__':
    unittest.main()
