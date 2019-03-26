import unittest
from resources import board

class TestingGamestate(unittest.TestCase):
    def setUp(self):
        self.gs = board.Board(10,10)

    def test_gamestate_regular_block_is_stable(self):
        self.assertEqual(self.gs.check_block(1,1), board.Block.STABLE)

    def test_gamestate_turn_block_stable_to_cracked(self):
        self.gs.change_block(2,2)
        self.assertEqual(self.gs.check_block(2,2), board.Block.CRACKED)


if __name__ == '__main__':
    unittest.main()
