#The logic for all gamestate code

from enum import Enum
import random, json
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
        self.turn = 0
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

    def randomly_generate_cracked_location(self, quantity):
        # We cannot generate more powerups than there are stable locations
        if quantity > len(self.stable_locations):
            quantity = len(self.stable_locations)
        if quantity > 0:
            for cracked_location in range(quantity): 
                avalible_locations = self.stable_locations.copy()
                if len(avalible_locations) > 0:
                    chosen_tile = (random.sample(avalible_locations, 1))
                    self.change_block(chosen_tile[0][0], chosen_tile[0][1])
            
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
        location_dict = {}
        for player in self.player_list.values():
            current_list = []
            if player.power in power_dict:
                current_list = power_dict[player.power]
            power_dict.setdefault(player.power, []).append(player)
            location_dict[player.current_location] = player


        ordered_p_d = sorted(power_dict.keys())

        for power_lvl in ordered_p_d:
            intended_moves = {}
            for player in power_dict[power_lvl]:
                move = self.find_intended_location(player)
                intended_moves.setdefault(move, []).append(player)
            
            
            final_moves = self.collision_check(intended_moves)
            
            for move, player in final_moves.items():
                if move in location_dict:
                    # If it is a different player that is in the way, push or dont move!
                    if not player == location_dict[move]:
                        # Power comparison
                        if player > location_dict[move]:
                            location_dict[move].current_location = self.push(location_dict[move], player.intended_movement(), location_dict)
                            del location_dict[move]
                        elif player < location_dict[move]:
                            move = player.current_location
                
                player.current_location = move
                location_dict[player.current_location] = player


    # Move a player into another space from another force. 
    # If there is anything blocking the way, the player is dead.
    def push(self, player, direction, current_locations_of_players):
        intended_location = (player.current_location[0], player.current_location[1])

        if direction == ["U"]: 
            #TODO: if the player is being pushed into the wall, or into another player, kill that boi
            if player.current_location[0] == 0:
                player.dead = True
                intended_location = (-1, -1)
            else:
                intended_location = (intended_location[0] - 1, intended_location[1])

        if direction == ["D"]:
            if player.current_location[0] == len(self.board[0]) - 1:
                player.dead = True
                intended_location = (-1, -1)
            else:
                intended_location = (intended_location[0] + 1, intended_location[1])

        if direction == ["L"]:
            if player.current_location[1] == 0:
                player.dead = True
                intended_location = (-1, -1)
            else:
                intended_location = (intended_location[0], intended_location[1] - 1)

        if direction == ["R"]:
            if player.current_location[1] == len(self.board[0]) - 1: 
                player.dead = True
                intended_location = (-1, -1)
            else:
                intended_location = (intended_location[0], intended_location[1] + 1)
        
        if intended_location in current_locations_of_players:
            player.dead = True
            intended_location = (-1, -1)

        return intended_location
                

    # Finds the space the given player would like to move. This function also safeguards to player from moving off the map.
    def find_intended_location(self, player):
        intended_location = (player.current_location[0], player.current_location[1])

        if (player.movement == ["U"]) and (player.current_location[0] > 0):
            intended_location = (intended_location[0] - 1, intended_location[1])

        if (player.movement == ["D"]) and (player.current_location[0] < len(self.board[0]) - 1):
            intended_location = (intended_location[0] + 1, intended_location[1])

        if (player.movement == ["L"]) and (player.current_location[1] > 0):
            intended_location = (intended_location[0], intended_location[1] - 1)

        if (player.movement == ["R"]) and (player.current_location[1] < len(self.board[0]) - 1):
            intended_location = (intended_location[0], intended_location[1] + 1)

        if player.movement == ["N"]:
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


    def complete_turn(self):
        self.transition_blocks()
        self.calculate_player_finished_positions()
        for player in self.player_list.values():
            if player.current_location in self.hole_locations:
                player.dead = True
            if player.current_location in self.powerup_locations:
                player.add_power(1)
                self.remove_powerup(player.current_location[0], player.current_location[1])
        self.randomly_generate_powerups(int(len(self.board[0]) / 5) + 1)
        self.randomly_generate_cracked_location(int(len(self.board[0]) / 3) + 1)

        self.turn += 1

        return self.get_full_gamestate()
        
        
    def get_full_gamestate(self):
        returned_json = {}

        returned_json["board_size"] = len(self.board[0])
        returned_json["turn"] = self.turn
        powerup_json = []
        for powerup_location in self.powerup_locations:
            powerup_json.append(self.coord_converter(powerup_location[0], powerup_location[1]))
        returned_json["powerup_locations"] = powerup_json

        cracked_json = []
        for cracked_location in self.cracked_locations:
            cracked_json.append(self.coord_converter(cracked_location[0], cracked_location[1]))
        returned_json["cracked_locations"] = cracked_json

        stable_json = []
        for stable_location in self.stable_locations:
            stable_json.append(self.coord_converter(stable_location[0], stable_location[1]))
        returned_json["stable_locations"] = stable_json

        hole_json = []
        for hole_location in self.hole_locations:
            hole_json.append(self.coord_converter(hole_location[0], hole_location[1]))
        returned_json["hole_locations"] = hole_json

        player_json = []
        player_list_copy = self.player_list.copy()
        for player in player_list_copy.values():
            player_quals = {}
            player_quals["id"] = player.id
            player_quals["current_location"] = self.coord_converter(player.current_location[0], player.current_location[1])
            player_quals["power"] = player.power
            player_quals["intended_move"] = player.movement
            if player.dead:
                player_quals["dead"] = "true"
                del self.player_list[player.id]
            else:
                player_quals["dead"] = "false"
                self.player_list[player.id].intended_movement = ["S"]
            player_json.append(player_quals)
            

        returned_json["player_list"] = player_json

        return(json.dumps(returned_json))

    def coord_converter(self, x, y):
        new_coord = {}
        new_coord["x"] = y
        new_coord["y"] = len(self.board[0]) - (x + 1) 
        return new_coord

    def coord_unconverter(self, x, y):
        normal_tup = ((len(self.board[0]) - (y + 1)), x)
        return normal_tup

    def recieve_game_state(self, json_string):
        # self.size = game_state_json["board_size"] = len(self.board[0])
        game_state_json = json.loads(json_string)
    
        self.board = [[Block() for x in range(game_state_json["board_size"])] for y in range(game_state_json["board_size"])]

        self.turn = game_state_json["turn"]

        powerup_list = []
        for powerup_location in game_state_json["powerup_locations"]:
            coord = self.coord_unconverter(powerup_location['x'], powerup_location['y'])
            self.board[coord[0]][coord[1]].has_powerup = True
            powerup_list.append(coord)
        self.powerup_locations = powerup_list

        cracked_list = []
        for cracked_location in game_state_json["cracked_locations"]:
            coord = self.coord_unconverter(cracked_location['x'], cracked_location['y'])
            self.board[coord[0]][coord[1]].block_state = BlockState.CRACKED
            cracked_list.append(coord)
        self.cracked_locations = cracked_list

        stable_list = []
        for stable_location in game_state_json["stable_locations"]:
            coord = self.coord_unconverter(stable_location['x'], stable_location['y'])
            stable_list.append(coord)
        self.stable_locations = stable_list

        hole_list = []
        for hole_location in game_state_json["hole_locations"]:
            coord = self.coord_unconverter(hole_location['y'], hole_location['y'])
            self.board[coord[0]][coord[1]].block_state = BlockState.HOLE
            hole_list.append(coord)
        self.hole_locations = hole_list

        for player in game_state_json["player_list"]:
            player_id = player["id"]
            if player_id in self.player_list:
                self.player_list[player_id].current_location = self.coord_unconverter(player["current_location"]["x"], player["current_location"]["y"])
            else:
                new_coord = self.coord_unconverter(player["current_location"]["x"], player["current_location"]["y"])
                self.assign_player_with_location(player_id, new_coord[0], new_coord[1])
            
            self.player_list[player_id].power = player["power"]
            self.player_list[player_id].inteneded_move = player["intended_move"]
            if player["dead"]  == "true":
                self.player_list[player_id].dead = "true"

            if player["dead"]  == "false":
                self.player_list[player_id].dead = "false"

                


