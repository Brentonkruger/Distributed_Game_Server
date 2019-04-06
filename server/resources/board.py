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
        power_dict = {}
        # print(self.player_list.values())
        for player in self.player_list.values():
            current_list = []
            if player.power in power_dict:
                current_list = power_dict[player.power]
            power_dict.setdefault(player.power, []).append(player)

        ordered_p_d = sorted(power_dict.keys())
        for power_lvl in ordered_p_d:
            intended_moves = {}
            for player in power_dict[power_lvl]:
                move = self.find_intended_location(player)
                intended_moves.setdefault(move, []).append(player)
            
            
            final_moves = self.collision_check(intended_moves)
            for move, player in final_moves.items():
                # TODO: If the move is going onto another player, push or squish
                player.current_location = move


                # BELOW IS THE CODE TO JUST GET THE PLAYERS MOVING WITH NO COLLISION DETECTION.
                #>>>> player.current_location = self.find_intended_location(player) <<<<<

                

            # Now that we have the list of where everyone would like to be, we resolve collisions.

            #TODO: Check for collisions or something based on these intended locations, rather than assign them
        
    # Finds the space the given player would like to move. This function also safeguards to player from moving off the map.
    def find_intended_location(self, player):
        intended_location = (player.current_location[0], player.current_location[1])

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

        return intended_location

    # Takes in a tuple of players and their intended locations, then checks for conflicts
    def collision_check(self, intended_moves):
        for location, player_list in intended_moves.items():
            if len(player_list) > 1:
                #Resolve the conflict
                for player in player_list:
                    intended_moves.setdefault(player.current_location, []).append(player)
                del intended_moves[location]
                intended_moves = self.collision_check(intended_moves)
                break
            else:
                intended_moves[location] = player_list[0]
        return intended_moves
    