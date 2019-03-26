import unittest
from resources import board

class TestingBoard(unittest.TestCase):
    def setUp(self):
        self.brd = board.Board(10,10)

    def test_gamestate_regular_block_is_stable(self):
        self.assertEqual(self.brd.check_block(1,1), board.Block.STABLE)

    def test_gamestate_turn_block_stable_to_cracked(self):
        self.brd.change_block(2,2)
        self.assertEqual(self.brd.check_block(2,2), board.Block.CRACKED)

    def test_powerup_assignment_to_powerup_location_fails(self):
        self.brd.add_powerup(3,3)
        self.assertFalse(self.brd.add_powerup(3,3))

    def test_powerup_assignment_to_legal_location(self):
        self.assertTrue(self.brd.add_powerup(3,3))


if __name__ == '__main__':
    unittest.main()
