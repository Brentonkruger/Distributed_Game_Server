#The logic for all gamestate code

from enum import Enum
import random
from . import player

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
        self.powerup_locations = set()
        self.player_list = {}
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
            self.powerup_locations.add((x,y))
            return True

    def remove_powerup(self, x, y):
        if (x,y) in self.powerup_locations:
            self.powerup_locations.remove((x,y))
        self.board[x][y].has_powerup = False

    def transition_blocks(self):
        copy_of_cracked_locations = self.cracked_locations.copy()
        for tup in copy_of_cracked_locations:
            self.change_block(tup[0],tup[1])
            self.remove_powerup(tup[0],tup[1])

    # Given some amount of powerups we want to generate, generate them on stable locations.
    def randomly_generate_powerups(self, quantity):
        # We cannot generate more powerups than there are stable locations
        if quantity > len(self.stable_locations):
            quantity = len(self.stable_locations)
        if quantity > 0:
            for powerup in range(quantity): 
                avalible_locations = self.stable_locations.difference(self.powerup_locations)
                avalible_locations = avalible_locations.difference(self.get_player_locations())
                if len(avalible_locations) > 0:
                    chosen_tile = (random.sample(avalible_locations, 1))
                    self.add_powerup(chosen_tile[0][0], chosen_tile[0][1])
            
    def assign_players(self, number_of_players):
        for value in range(number_of_players):
            self.assign_player(value)

    # Assigns a player to a location that is on stable ground with no other players
    def assign_player(self, player_id):
        chosen_tile = (random.sample(self.stable_locations.difference(self.get_player_locations()), 1))
        newPlayer = player.Player(player_id)
        newPlayer.current_location = (chosen_tile[0][0], chosen_tile[0][1])
        self.player_list[player_id] = newPlayer

    def assign_player_with_location(self, player_id, x, y):
        newPlayer = player.Player(player_id)
        newPlayer.current_location = (x, y)
        self.player_list[player_id] = newPlayer

    def get_player_locations(self):
        player_locations = []
        for key, player in self.player_list.items():
            player_locations.append(player.current_location)
        return player_locations

    def get_player_by_id(self, player_id):
        return self.player_list[player_id]
        

    def set_player_movement_direction(self, player_id, move_list):
        requested_player = self.get_player_by_id(player_id)
        if not requested_player == None:
            requested_player.change_movement(move_list)
        else:
            return False

    def calculate_player_finished_positions(self):

        sorted_player_list_by_power = sorted(self.player_list.values(), key=lambda player: player.power, reverse=True)
        # From highest to lowest in power amount
        for player in sorted_player_list_by_power:
            intended_location = (player.current_location[0], player.current_location[1])
            # If we wanted to do multiple moves a turn, we would have a for loop for each movement here
            if (player.intended_movement() == ["U"]) and (player.current_location[0] > 0):
                intended_location = (intended_location[0] - 1, intended_location[1])

            if (player.intended_movement() == ["D"]) and (player.current_location[0] < len(self.board[0]) - 1):
                intended_location = (intended_location[0] + 1, intended_location[1])

            if (player.intended_movement() == ["L"]) and (player.current_location[1] > 0):
                intended_location = (intended_location[0], intended_location[1] - 1)

            if (player.intended_movement() == ["R"]) and (player.current_location[1] < len(self.board[0]) - 1):
                intended_location = (intended_location[0], intended_location[1] + 1)

            if player.intended_movement() == ["N"]:
                intended_location = (intended_location[0], intended_location[1])

            #TODO: Check for collisions or something based on these intended locations, rather than assign them
            player.current_location = intended_location
            
            
            

        