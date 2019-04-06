import unittest
from resources import board

class TestingBoard(unittest.TestCase):


    # Need numerous tests to get the game state proven to be working. 
    # 1. Create a board, with randomly assigned player locations, powerup locations, and an amount of "cracked" tiles
    # 2. Given some inputed movements, create a new valid gamestate


    def test_gamestate_regular_block_is_stable_10x10(self):
        # Initialize game size
        self.brd = board.Board(10)
        
        # Ensure that the two corners are both stable, and the stable_locations set is equal to 100
        self.assertEqual(self.brd.check_block_state(0,0), board.BlockState.STABLE)
        self.assertEqual(self.brd.check_block_state(9,9), board.BlockState.STABLE)
        self.assertEqual(len(self.brd.stable_locations), 100)

    def test_gamestate_regular_block_is_stable_20x20(self):
        # Initialize game size
        self.brd = board.Board(20)
        
        # Ensure that the two corners are both stable, and the stable_locations set is equal to 100
        self.assertEqual(self.brd.check_block_state(0,0), board.BlockState.STABLE)
        self.assertEqual(self.brd.check_block_state(19,19), board.BlockState.STABLE)
        self.assertEqual(len(self.brd.stable_locations), 400)

    def test_gamestate_complete_transition_of_block(self):
        # Initialize game size
        self.brd = board.Board(10)

        # Checking the inital gamestate initialization
        self.assertEqual(self.brd.check_block_state(2,2), board.BlockState.STABLE)
        self.assertTrue((2,2) in self.brd.stable_locations)

        # Checking the state after we do another change to cracked
        self.brd.change_block(2,2)
        self.assertEqual(self.brd.check_block_state(2,2), board.BlockState.CRACKED)
        self.assertFalse((2,2) in self.brd.stable_locations)
        self.assertEqual(self.brd.cracked_locations, {(2,2)})

        # Checking the state after we do the final change to hole
        self.brd.change_block(2,2)
        self.assertEqual(self.brd.check_block_state(2,2), board.BlockState.HOLE)
        self.assertFalse(self.brd.cracked_locations)
        self.assertEqual(self.brd.hole_locations, {(2,2)})

    def test_gamestate_powerup_addition_to_stable(self):
        # Initialize game size
        self.brd = board.Board(10)
        self.assertFalse(self.brd.check_block(1,1).has_powerup)
        self.brd.add_powerup(1,1)
        self.assertTrue(self.brd.check_block(1,1).has_powerup)

    def test_gamestate_powerup_addition_to_cracked(self):
        # Initialize game size
        self.brd = board.Board(10)
        # Set the block to cracked
        self.brd.change_block(1,1)
        self.assertFalse(self.brd.check_block(1,1).has_powerup)
        self.brd.add_powerup(1,1)
        self.assertTrue(self.brd.check_block(1,1).has_powerup)

    def test_gamestate_powerup_addition_to_hole(self):
        # Initialize game size
        self.brd = board.Board(10)
        # Set the block to hole
        self.brd.change_block(1,1)
        self.brd.change_block(1,1)
        self.assertFalse(self.brd.check_block(1,1).has_powerup)
        self.brd.add_powerup(1,1)
        # Doesnt work because the powerup cannot exist over a hole
        self.assertFalse(self.brd.check_block(1,1).has_powerup)

    def test_gamestate_transition_stable_with_powerup(self):
        # Initialize game size
        self.brd = board.Board(10)
        self.assertFalse(self.brd.check_block(1,1).has_powerup)
        self.brd.add_powerup(1,1)
        self.assertTrue(self.brd.check_block(1,1).has_powerup)
        self.brd.change_block(1,1)
        self.assertTrue(self.brd.check_block(1,1).has_powerup)

    def test_gamestate_transition_cracked_states(self):
        # Initialize game size
        self.brd = board.Board(10)

        # Set two blocks to cracked, then run transition function

        self.brd.change_block(1,1)
        self.brd.change_block(1,2)

        self.assertEqual(len(self.brd.cracked_locations), 2)
        self.assertEqual(len(self.brd.hole_locations), 0)

        self.brd.transition_blocks()

        self.assertEqual(len(self.brd.hole_locations), 2)
        self.assertEqual(len(self.brd.cracked_locations), 0)

    def test_gamestate_transition_cracked_with_powerup(self):
        # Initialize game size
        self.brd = board.Board(10)

        # Set two blocks to cracked, then run transition function
        self.brd.change_block(1,1)
        self.brd.add_powerup(1,1)
        self.assertTrue(self.brd.check_block(1,1).has_powerup)
        self.brd.transition_blocks()
        self.assertFalse(self.brd.check_block(1,1).has_powerup)

    def test_gamestate_generate_powerup(self):
        # Initialize game size
        self.brd = board.Board(10)
        self.brd.randomly_generate_powerups(1)
        self.assertEqual(len(self.brd.powerup_locations), 1)

    def test_gamestate_generate_3_powerups(self):
        # Initialize game size
        self.brd = board.Board(10)
        self.brd.randomly_generate_powerups(3)
        self.assertEqual(len(self.brd.powerup_locations), 3)

    def test_gamestate_generate_powerup_with_less_stable(self):
        # Initialize game size
        self.brd = board.Board(1)
        self.brd.randomly_generate_powerups(3)
        self.assertEqual(len(self.brd.powerup_locations), 1)

    def test_gamestate_generate_powerup_with_no_stable(self):
        # Initialize game size
        self.brd = board.Board(1)
        self.brd.change_block(0,0)
        self.brd.randomly_generate_powerups(3)
        self.assertEqual(len(self.brd.powerup_locations), 0)
        
    def test_gamestate_generate_player_positions(self):
        self.brd = board.Board(10)
        self.brd.assign_players(5)
        self.assertEqual(len(self.brd.get_player_locations()), 5)

    def test_gamestate_generate_powerups_with_many_players(self):
        self.brd = board.Board(2)
        self.brd.assign_players(3)
        # Try to gen more powerups then there is space.
        self.brd.randomly_generate_powerups(3)
        self.assertEqual(len(self.brd.powerup_locations), 1)
    
    def test_gamestate_move_players_up(self):
        self.brd = board.Board(5)
        self.brd.assign_player_with_location(0, 4, 4)
        self.brd.set_player_movement_direction(0, ["U"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["U"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (3,4))

        self.brd.set_player_movement_direction(0, ["U"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["U"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (2,4))

        self.brd.set_player_movement_direction(0, ["U"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["U"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (1,4))

        self.brd.set_player_movement_direction(0, ["U"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["U"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (0,4))

        self.brd.set_player_movement_direction(0, ["U"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["U"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (0,4))

    def test_gamestate_move_players_down(self):
        self.brd = board.Board(5)
        self.brd.assign_player_with_location(0, 0, 4)
        self.brd.set_player_movement_direction(0, ["D"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["D"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (1,4))

        self.brd.set_player_movement_direction(0, ["D"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["D"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (2,4))

        self.brd.set_player_movement_direction(0, ["D"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["D"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (3,4))

        self.brd.set_player_movement_direction(0, ["D"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["D"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (4,4))

        self.brd.set_player_movement_direction(0, ["D"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["D"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (4,4))

    def test_gamestate_move_players_right(self):
        self.brd = board.Board(3)
        self.brd.assign_player_with_location(0, 0, 0)

        self.brd.set_player_movement_direction(0, ["R"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["R"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (0,1))

        self.brd.set_player_movement_direction(0, ["R"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["R"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (0,2))

        self.brd.set_player_movement_direction(0, ["R"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["R"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (0,2))

    def test_gamestate_move_players_left(self):
        self.brd = board.Board(3)
        self.brd.assign_player_with_location(0, 0, 2)

        self.brd.set_player_movement_direction(0, ["L"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["L"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (0,1))

        self.brd.set_player_movement_direction(0, ["L"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["L"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (0,0))

        self.brd.set_player_movement_direction(0, ["L"])
        self.assertEqual(self.brd.get_player_by_id(0).intended_movement(),["L"]) 
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (0,0))
        
    def test_gamestate_move_with_collisions_of_same_power(self):
        self.brd = board.Board(3)
        self.brd.assign_player_with_location(0, 0, 2)
        self.brd.assign_player_with_location(1, 2, 2)
        self.brd.assign_player_with_location(2, 1, 1)

        self.brd.set_player_movement_direction(0, ["D"])
        self.brd.set_player_movement_direction(1, ["U"])
        self.brd.set_player_movement_direction(2, ["R"])
        self.brd.calculate_player_finished_positions()
        self.assertEqual(self.brd.get_player_by_id(0).current_location, (0,2))
        self.assertEqual(self.brd.get_player_by_id(1).current_location, (2,2))
        self.assertEqual(self.brd.get_player_by_id(2).current_location, (1,1))

    def test_gamestate_move_into_higher_power(self):
        self.brd = board.Board(2)
        self.brd.assign_player_with_location(0, 0, 2)
        self.brd.assign_player_with_location(1, 1, 2)

        # Player 1 is stronger, and will go first.
        self.brd.get_player_by_id(0).add_power(1)

        self.brd.set_player_movement_direction(0, ["S"])
        self.brd.set_player_movement_direction(1, ["U"])

        self.brd.calculate_player_finished_positions()

        self.assertEqual(self.brd.get_player_by_id(0).current_location, (0,2))
        self.assertEqual(self.brd.get_player_by_id(1).current_location, (1,2))

    def test_gamestate_move_into_lower_power_push(self):
        self.brd = board.Board(3)
        self.brd.assign_player_with_location(0, 1, 2)
        self.brd.assign_player_with_location(1, 2, 2)

        # Player 1 is stronger, and will go first.
        self.brd.get_player_by_id(1).add_power(1)

        self.brd.set_player_movement_direction(0, ["S"])
        self.brd.set_player_movement_direction(1, ["U"])

        self.brd.calculate_player_finished_positions()

        self.assertEqual(self.brd.get_player_by_id(0).current_location, (0,2))
        self.assertEqual(self.brd.get_player_by_id(1).current_location, (1,2))

    def test_gamestate_move_into_lower_power_squish_from_wall(self):
        self.brd = board.Board(2)
        self.brd.assign_player_with_location(0, 0, 2)
        self.brd.assign_player_with_location(1, 1, 2)

        # Player 1 is stronger, and will go first.
        self.brd.get_player_by_id(1).add_power(1)

        self.brd.set_player_movement_direction(0, ["S"])
        self.brd.set_player_movement_direction(1, ["U"])

        self.brd.calculate_player_finished_positions()

        self.assertTrue(self.brd.get_player_by_id(0).dead)
        self.assertEqual(self.brd.get_player_by_id(1).current_location, (0,2))

    def test_gamestate_move_into_lower_power_squish_from_player(self):
        self.brd = board.Board(3)
        self.brd.assign_player_with_location(0, 1, 2)
        self.brd.assign_player_with_location(1, 2, 2)
        self.brd.assign_player_with_location(2, 0, 2)

        # Player 1 is stronger, and will go first.
        self.brd.get_player_by_id(1).add_power(1)

        self.brd.set_player_movement_direction(0, ["S"])
        self.brd.set_player_movement_direction(1, ["U"])

        self.brd.calculate_player_finished_positions()

        self.assertTrue(self.brd.get_player_by_id(0).dead)
        self.assertEqual(self.brd.get_player_by_id(1).current_location, (1,2))

    def test_player_powerup_pickup(self):
        self.brd = board.Board(3)
        self.brd.assign_player_with_location(0, 1, 2)
        self.brd.assign_player_with_location(1, 2, 2)

        self.brd.set_player_movement_direction(0, ["L"])
        self.brd.set_player_movement_direction(1, ["U"])

        # Make a hole where player with id 1 is going.
        self.brd.change_block(1,2)

        # Make a powerup where player with id 0 is going.
        self.brd.add_powerup(1,1)
        self.brd.complete_turn()

        self.assertEqual(self.brd.get_player_by_id(0).current_location, (1,1))
        self.assertEqual(self.brd.get_player_by_id(0).power, 1)

        # 1 because one was picked up, and one was spawned.
        self.assertEqual(len(self.brd.powerup_locations), 1)

        self.assertEqual(self.brd.get_player_by_id(1).current_location, (1,2))
        self.assertTrue(self.brd.get_player_by_id(1).dead)
        


        self.brd.complete_turn()


if __name__ == '__main__':
    unittest.main()
