from enum import Enum
import ipaddress
import asyncio
import socket
import secrets
import json
from aiohttp import web
import aiohttp
import random
from . import board

class State(Enum):
    NORMAL = 0
    VIEW_CHANGE = 1
    RECOVERING = 2

class Message():
    def __init__(self, operation_number, msg_body, recieved_backups = None, sent_to_client = False):
        if recieved_backups == None:
            self.recieved_backups = {}
        else:
            self.recieved_backups = recieved_backups
        self.operation_number = operation_number
        self.msg_body = msg_body
        self.sent_to_client = False
    

    def recieve_backup(self, backup_ip):
        if not backup_ip in self.recieved_backups:
            self.recieved_backups[backup_ip] = True
            return len(self.recieved_backups)
        else:
            return -1

    def client_sent(self):
        self.sent_to_client = True

    def get_message_number(self):
        return self.operation_number
 
    def get_message_body(self):
        return self.msg_body

class MessageEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Message):
            return {
            "recieved_backups": obj.recieved_backups,
            "operation_number": obj.operation_number, 
            "msg_body": obj.msg_body, 
            "sent_to_client": obj.sent_to_client}
        return json.JSONEncoder.default(self, obj)
    
class Timer:
    def __init__(self, timeout, callback, loop):
        self._timeout = timeout
        self._callback = callback
        self._loop = loop
        # self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        await self._callback()

    def cancel(self):
        self._task.cancel()
    
    def start(self, timeout = None, callback = None):
        if callback is not None:
            self.callback = callback
        if timeout is not None:
            self.timeout = timeout
        self._task = asyncio.ensure_future(self._job(), loop=self._loop)

    def restart(self):
        self._task.cancel()
        self._task = asyncio.ensure_future(self._job(), loop=self._loop)

class replica:
    
    def __init__(self, routing_ip):
        self.current_state = State.NORMAL
        self.other_replicas = []
        self.all_replicas = []
        self.client_list = {}
        self.request_ok = {}
        self.ready_list = {}
        self.routing_layer = routing_ip
        self.n_view = 0
        self.n_commit = 0
        self.n_operation = 0
        self.n_recovery_messages = 0
        self.start_count = 0
        self.n_start_view_change_messages = 0
        self.n_do_view_change_messages = 0
        self.this_turns_responses = 0

        # Most likely this has to change to a dictionary
        self.n_gamestate_responses = 0
        self.start_view_change_sent = False
        self.primary_recovery_response = False
        self.game_running = False
        self.current_turn = 0
        self.log = {}
        self.game_board = None

        #get Ip of the local computer
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        #s.getsockname() has the local ip address at [0] and the local port at [1]
        self.local_ip = s.getsockname()[0]
        print("IP address: ", self.local_ip)
        s.close()
        self.all_replicas.append(self.local_ip)
        

        #start the local loop to allow for asyncio (starts the server)       
        self.loop = asyncio.get_event_loop()

        self.loop.create_task(self.http_server_start())
        self.loop.create_task(self.request_primary_ip())

        try:
            self.loop.run_forever()
        except ConnectionError:
            pass
        except:
            self.loop.close()
        
    async def start_recovery(self):
        self.current_state = State.RECOVERING
        self.n_recovery_messages = 0

        # self.timer.cancel()

        #Send broadcast to all replicas with random nonce and its address
        self.recovery_nonce = secrets.randbits(32)
        message = json.dumps({
            "Type": "Recover",
            "N_replica": self.local_ip,
            "Nonce": self.recovery_nonce
	    })
        print("Recovery started...")
        await self.replica_broadcast("post", "Recover", message)
        print("Recovered")

    async def recovery_response(self, request):
        if self.current_state == State.RECOVERING:
            
            msg = await request.json()
            if type(msg) == dict:
                text = msg
            else:
                text = json.loads(msg)
            print("Recovery message received from: ", request.remote)
            if text["Nonce"] == self.recovery_nonce:
                self.n_recovery_messages +=1
                if request.remote == self.primary:
                    # save state info
                    self.game_board = board.Board(1)                    
                    self.log = {k:Message(**v) for k,v in json.loads(text["Log"]).items()}
                    self.n_commit = text["N_Commit"]
                    self.n_operation = text["N_Operation"]
                    self.n_view = text["N_View"]
                    self.primary_recovery_response = True
                if self.n_recovery_messages >= int(len(self.other_replicas)/2) and self.primary_recovery_response:
                    self.n_recovery_messages = 0
                    self.primary_recovery_response = False
                    self.current_state = State.NORMAL
        return web.Response()

    async def start_view_change(self, request):
        #recieves this message from other nodes to start the process.
        try:
            self.timer.cancel()
        except:
            pass

        if self.current_state != State.VIEW_CHANGE:
            self.current_state = State.VIEW_CHANGE
            self.n_view += 1   

        # Check to see if view number is the same
        msg = await request.json()
        if type(msg) == dict:
            text = msg
        else:
            text = json.loads(msg)
        print("View change message received from ", request.remote, ". Starting view change to ", self.n_view)

        if self.n_view < text["N_View"]:
            if not self.start_view_change_sent:
                message = json.dumps({
                    "N_View": self.n_view,
                    "N_replica": self.local_ip})
                await self.replica_broadcast("post", "StartViewChange", message)
                self.start_view_change_sent = True
            self.n_start_view_change_messages += 1
            
        if self.n_start_view_change_messages >= int(len(self.other_replicas)/2):
            msg = json.dumps({
                "Type": "DoViewChange",
                "N_View": self.n_view,
                "Log": json.dumps(self.log, cls = MessageEncoder),
                "N_View_Old": self.n_view-1,
                "N_Operation": self.n_operation,
                "N_Commit": self.n_commit,
                "N_replica": self.local_ip
                })
            # Send DoViewChange to new primary
            self.primary = self.get_new_primary_replica(self.primary)
            print("View change started")
            await self.send_message(self.primary, "post", "DoViewChange", msg)
        return web.Response()

    async def send_view_change(self):
        #change to view change mode
        #send out initial view change message
        self.current_state = State.VIEW_CHANGE
        self.n_view += 1
        message = json.dumps({
            "N_View": self.n_view,
            "N_replica": self.local_ip})
        await self.replica_broadcast("post", "StartViewChange", message)
        self.start_view_change_sent = True

    async def do_view_change(self, request):
        # If replica is primary, wait for f + 1 DoViewChange responses and update information
        if self.primary == self.local_ip:
            msg = await request.json()
            if type(msg) == dict:
                text = msg
            else:
                text = json.loads(msg)
            #update the primary if behind 
            if self.n_view <= text["N_View"]:
                if self.n_operation < text["N_Operation"]:
                    self.log = {k:Message(**v) for k,v in json.loads(text["Log"]).items()}
                    self.n_operation = text["N_Operation"]
                    self.n_commit = text["N_Commit"]

            if self.n_do_view_change_messages >= int(len(self.all_replicas) / 2):
                # Change status back to normal and send startview message to other replicas
                self.current_state = State.NORMAL
                # StartView json
                startview_message = json.dumps({
                    "Type": "StartView",
                    "N_View": self.n_view,
                    "Log": json.dumps(self.log, cls = MessageEncoder),
                    "N_Operation": self.n_operation,
                    "N_Commit": self.n_commit
                })

                # Broadcast message to other replicas
                await self.replica_broadcast("post", "StartView", startview_message)
                msg = json.dumps({"Type": "New_Primary",
                    "IP": self.local_ip})
                self.session.post("http://" + self.routing_layer + ":5000/NewPrimary", data=msg)
                self.timer.start(7, self.send_commit)

    async def send_commit(self):
        #send out the commit message as a heartbeat
        msg = json.dumps({"Type": "Commit", "N_View": self.n_view, "N_Commit": self.n_commit})
        await self.replica_broadcast("post", "Commit", msg)
        self.timer.start()

    async def replica_broadcast(self, req_type, req_location, msg):
        for rep in self.other_replicas:
            await self.send_message(str(rep),req_type, req_location, msg)

    async def request_primary_ip(self):
        # start up the game, and get the current state of the game.
        resp = await self.session.get("http://" + self.routing_layer + ":5000/Join")
        txt = await resp.text()

        a_resp = json.loads(txt)
        self.primary = a_resp['Primary_IP']
        if a_resp['Primary_IP'] != self.local_ip:
            self.other_replicas.append(a_resp['Primary_IP'])
            self.all_replicas.append(a_resp['Primary_IP'])

            #connect to primary and ask for updated replica list
            msg = json.dumps({"Type": "GetReplicaList", "IP": self.local_ip})
            await self.send_message(self.primary, "post", "GetReplicaList", msg)
            
        else:
            #start a timer to send out a commit message (basically as a heartbeat)
            self.timer = Timer(5, self.send_commit, self.loop)
            self.timer.start(5, self.send_commit)

    async def get_new_primary_replica(self, old_ip):
        index = self.all_replicas.index(old_ip)
        return self.all_replicas[(index + 1) % len(self.all_replicas)]
        
    async def send_message(self, ip_addr, req_type, req_location, data):
        if req_type == "post":
            await self.session.post("http://" + ip_addr + ":9999/" + req_location, data = data)
        if req_type == "get":
            await self.session.get("http://" + ip_addr + ":9999/" + req_location, data = data)
            
    async def player_move(self, request):
        #check if the move has already been made (op number)
        msg = await request.json()
        if type(msg) == dict:
            text = msg
        else:
            text = json.loads(msg)
        #primary sends out player move to backups, they add into the gamestate
        if self.local_ip == self.primary:
            
            self.timer.cancel()
            # add fields needed for the replicas (commit number op number etc.)
            self.n_operation += 1
            msg = json.dumps({
                "Type":"PlayerMovement",
                "Operation": text['Operation'],
                "Client_ID": text['Client_ID'],
                "N_Request": text['N_Request'],
                "N_Operation": self.n_operation,
                "N_Commit": self.n_commit,
                "N_View": self.n_view})

            self.request_ok[self.n_operation] = 0
            self.log[self.n_operation] = Message(self.n_operation, msg)
            await self.replica_broadcast("post", "PlayerMovement", msg)
            self.timer.start()
            return web.Response()
        
        #backups receive the player move and adds it to the gamestate, then replies when it's finished
        else:
            self.timer.cancel()
            if text["N_Operation"] > self.n_operation:
                self.n_operation = text["N_Operation"]
            if text["N_Commit"] > self.n_commit:
                self.n_commit = text["N_Commit"]
            if text["N_View"] > self.n_view:
                self.start_state_transfer()
            self.game_board.get_player_by_id(text["Client_ID"]).change_movement(text["Operation"])
            # add to the log
            self.log[self.n_operation] = Message(self.n_operation, text)
            await self.send_message(self.primary, "post", "PlayerMoveOK", json.dumps(text))

            self.timer.start()
            return web.Response()
    
    async def player_move_ok(self, request):
        msg = await request.json()
        if type(msg) == dict:
            text = msg
        else:
            text = json.loads(msg)

        if self.local_ip == self.primary:
            #TODO: overhaul to make use of the new logs
            backup_responses = self.log[text["N_Operation"]].recieve_backup(request.remote)
            if backup_responses >= (len(self.other_replicas)/2) and not self.log[text["N_Operation"]].sent_to_client:
                self.game_board.get_player_by_id(text["Client_ID"]).change_movement(text["Operation"])
                #we are using this as a quorum check among the replicas as these messages never get sent to clients.
                self.log[text["N_Operation"]].client_sent()
   
                #This updates the commit number if we can. (other older messages might not be updated yet)
                i = self.n_commit + 1
                lower_found = True
                while i <= self.n_operation and lower_found:
                    if self.log[i].sent_to_client:
                        self.n_commit = i
                        i += 1
                    else:
                        lower_found = False
            return web.Response()
        
    async def turn_cutoff(self):
        if self.local_ip == self.primary:
            self.this_turns_responses = 0
            self.current_turn += 1
            print("Doing turn number: ", str(self.current_turn))
            self.game_board.complete_turn()
            #Add a message to the log.
            self.n_operation += 1
            msg = json.dumps({
                "Type": "ComputeGamestate",
                "N_Operation": self.n_operation,
                "N_Commit": self.n_commit,
                "N_View": self.n_view,
                "Gamestate": self.game_board.get_full_gamestate()
            })
            self.log[self.n_operation] = Message(self.n_operation, msg)
            await self.replica_broadcast("post", "ComputeGamestate", msg) 


    async def client_join(self, request):
        msg = await request.json()
        if type(msg) == dict:
            text = msg
        else:
            text = json.loads(msg)
        #client has joined up
        #check for a running game
        if self.local_ip == self.primary:
            if not self.game_running:
                if text["Client_IP"] not in self.client_list:
                    self.client_list[text["Client_IP"]] = len(self.client_list)
                    print("Adding Client: " + str(text["Client_IP"]))
                # TODO: Broadcast the request across replicas, this means implement this function if the replica is not the server.
                    replica_msg = json.dumps({
                        "Type": "ClientJoin",
                        "Client_ID": self.client_list[text["Client_IP"]],
                        "Client_IP": text["Client_IP"],
                        "N_Request": text['N_Request']})
                    await self.replica_broadcast("post", "ClientJoin", replica_msg)
                    #this prepares the message to the client
                    self.ready_list[self.client_list[text["Client_IP"]]] = 0
                resp = json.dumps({
                    "Type": "ClientJoinOK",
                    "Client_ID": self.client_list[text["Client_IP"]],
                    "N_Request": text['N_Request']})
                return web.Response(body = resp)
                
            else:
                return web.Response(status = 400)
        else:
            #replica portion
            if text["Client_IP"] not in self.client_list:
                    self.client_list[text["Client_IP"]] = text["Client_ID"]
                    print("Added Client: " + str(text["Client_IP"]))
            return web.Response()
           
    async def readied_up(self, request):
        #add the user's ready state

        msg = await request.json()
        if type(msg) == dict:
            text = msg
        else:
            text = json.loads(msg)
        #primary sends backups request, who respond I guess?
        if self.local_ip == self.primary:
            await self.replica_broadcast("post", "Ready", json.dumps(text))
        else:
            await self.send_message(self.primary, "post", "ReadyConfirm", json.dumps({"Type": "ReadyConfirm", "Client_ID": text["Client_ID"]}))
        return web.Response()
        
    async def ready_confirm(self, request):
        msg = await request.json()
        if type(msg) == dict:
            text = msg
        else:
            text = json.loads(msg)
        cid = text["Client_ID"]
        self.ready_list[cid] += 1
        can_start = True
        for i in self.ready_list.values():
            if i < len(self.other_replicas)/2:
                can_start = False
        if can_start:
            for key, val in self.ready_list.items():
                self.ready_list[key] = 0
            await self.start_game()
        return web.Response()
  
    async def start_game(self):
        #finalize the servers on game start
        #send the message to the clients to begin the game
        self.game_running = True

        if self.local_ip == self.primary:
            size = int(len(self.client_list)) * 4

            self.game_board = board.Board(size)
            self.game_board.assign_players(len(self.client_list))
            gamestate = self.game_board.get_full_gamestate()
            
            start = json.dumps({
                "Type": "GameStart",
                "GameState": gamestate
            })
            # TODO: Add to the log
            await self.replica_broadcast("post", "StartConfirm", start)
            # self.session.post("http://" + self.routing_layer + ":5000/GameStart", data=start)
            # 

    async def start_confirm(self,request):
        msg = await request.json()
        if type(msg) == dict:
            text = msg
        else:
            text = json.loads(msg)
        # cid = text["Client_ID"]
        
        if self.local_ip != self.primary:
            can_start = True
            for i in self.ready_list.values():
                if i < len(self.other_replicas)/2:
                    can_start = False
            if can_start:
                for key, val in self.ready_list.items():
                    self.ready_list[key] = 0
                self.game_board = board.Board(1)
                self.game_board.recieve_game_state(text["GameState"])
                #respond with startconfirm to server
                await self.send_message(self.primary, "post", "StartConfirm", text["GameState"])
            return web.Response()
        else:
            self.start_count += 1
            if self.start_count >= len(self.other_replicas)/2:
                msg = json.dumps({
                    "Type": "GameUpdate", 
                    "GameState": text
                    })
                self.turn_timer = Timer(7, self.turn_cutoff, self.loop)
                self.turn_timer.start()
                await self.session.post("http://" + self.routing_layer + ":5000/GameUpdate", data=msg)
            return web.Response()

    async def compute_gamestate(self, request):
        #compute gamestate and return message
        # If primary, send bad response

        msg = await request.json()
        if type(msg) == dict:
            text = msg
        else:
            text = json.loads(msg)

        if self.primary == self.local_ip:
            return web.Response(status = 400, body = json.dumps({"Primary_IP": self.primary}))
        # Send response to primary
        else:
            self.game_board.recieve_game_state(text["Gamestate"])

            og_game_state = self.game_board.get_full_gamestate()
            update = json.dumps({
                "Type": "Gamestate",
                "N_View": text["N_View"],
                "N_Operation": text["N_Operation"],
                "N_Commit": text["N_Commit"],
                "GameBoard": json.loads(og_game_state)
            })
            await self.send_message(self.primary, "post", "Gamestate", update)
        return web.Response()
    
    async def receive_gamestate(self, request):
        # Only primary should receive gamestate
        if self.primary == self.local_ip:
            msg = await request.json()
            if type(msg) == dict:
                text = msg
            else:
                text = json.loads(msg)
            # Once enough responses received, send to clients with final gamestate
            clients_approved = self.log[text["N_Operation"]].recieve_backup(request.remote)
            if clients_approved >= int(len(self.other_replicas) / 2) and not self.log[text["N_Operation"]].sent_to_client:
                new_gamestate = json.dumps({
                    "Type": "GameUpdate",
                    "GameState": json.loads(self.game_board.get_full_gamestate())
                })
                
                await self.session.post("http://" + self.routing_layer + ":5000/GameUpdate", data=new_gamestate)
                #update that client has had the message sent to prevent other spurious messages
                self.log[text["N_Operation"]].client_sent()

                #This updates the commit number if we can. (other older messages might not be updated yet)
                i = self.n_commit + 1
                lower_found = True
                while i <= self.n_operation and lower_found:
                    if self.log[i].sent_to_client:
                        self.n_commit = i
                        i += 1
                    else:
                        lower_found = False

                self.turn_timer.start()
            return web.Response()

        # If not primary, send address of primary to replica
        else:
            return web.Response(status = 400, body = json.dumps({"Primary_IP": self.primary}))

    async def apply_commit(self, request):
        #recieve the commit message, and apply if necessary.
        print("Commit received")
        self.timer.cancel()
        msg = await request.json()
        if type(msg) == dict:
            text = msg
        else:
            text = json.loads(msg)
        if text["N_View"] > self.n_view or text["N_Commit"] > self.n_commit:
            await self.start_state_transfer()
        self.timer.start()
        #don't update client about this one.
        return web.Response()
            
    async def start_view(self, request):
        msg = await request.json()
        if type(msg) == dict:
            text = msg
        else:
            text = json.loads(msg)
        self.n_view = text['N_View']
        self.log = {k:Message(**v) for k,v in json.loads(text["Log"]).items()}
        self.n_operation = text['N_Operation']
        self.n_commit = text['N_Commit']
        self.primary = request.remote
        self.current_state = State.NORMAL
        return web.Request()
    
    async def start_state_transfer(self):
        #send state transfer
        #set operation back to where things were still ok
        self.n_operation = self.n_commit
        msg = {
            "Type": "GetState",
            "N_View":self.n_view,
            "N_Operation":self.n_operation,
            "N_Replica":self.local_ip
        }
        tmp_list = self.other_replicas
        resp = await self.send_message(random.sample(tmp_list, 1)[0], "post", "GetState", msg)
        #update state
        msg = await resp.text()
        if type(msg) == dict:
            text = msg
        else:
            text = json.loads(msg)
        self.n_view = text['N_View']
        self.n_operation = text['N_Operation']
        self.n_commit = text['N_Commit']
        self.log = {k:Message(**v) for k,v in json.loads(text["Log"]).items()}
        
    async def get_state(self, request):

        msg = json.dumps({
            "Type": "NewState",
            "N_View":self.n_view,
            "Log": json.dumps(self.log, cls = MessageEncoder),
            "N_Operation":self.n_operation,
            "N_Commit":self.n_commit})
            
        return web.Response(body = msg)

    async def recovery_help(self, request):
        if self.current_state != State.RECOVERING:        
            #send back the recover message
            msg = await request.json()
            if type(msg) == dict:
                text = msg
            else:
                text = json.loads(msg)
            if self.primary == self.local_ip:

                #if self.game_board == None:
                 #   gameboard = None
                #else:
                 #   gameboard = json.loads(self.game_board.get_full_gamestate())
                #return the intense answer
                reply = json.dumps({
                    "Type": "RecoveryResponse",
                    "N_View": self.n_view,
                    "Nonce": text['Nonce'],
                    "Log": json.dumps(self.log, cls = MessageEncoder),
                    "N_Operation": self.n_operation,
                    "N_Commit": self.n_commit
                })
                print("Sending Primary Recovery Message...")
                await self.send_message(request.remote, "post", "RecoveryResponse", reply)
                return web.Response()
            else:
                #return the small answer
                payload = json.dumps({
                    "Type": "RecoveryResponse",
                    "N_View":self.n_view,
                    "Nonce":text['Nonce'],
                    "Log":"Nil",
                    "N_Operation":"Nil",
                    "N_Commit":"Nil"})
                print("Sending Backup Recovery Message...")
                await self.send_message(request.remote, "post", "RecoveryResponse", payload)
                return web.Response()
        else:
            return web.Response(status = 400)

    async def replica_list(self, request):
        #format the replica list and return it to the backup
        if self.local_ip == self.primary:
            if request.remote != self.local_ip:
                if request.remote not in self.all_replicas:
                    self.all_replicas.append(request.remote)
                    print("Added\t" + request.remote)
                if request.remote not in self.other_replicas:
                    self.other_replicas.append(request.remote)
            body = json.dumps({
                "Type": "UpdateReplicaList", 
                "Replica_List": [i for i in self.all_replicas], 
                "N_Commit": self.n_commit,
                "N_Operation": self.n_operation,
                "N_View": self.n_view})
            await self.replica_broadcast("post", "UpdateReplicaList", body)
            
            return web.Response()
        else: 
            return web.Response(status = 400, body = json.dumps({"Primary_IP": self.primary}))

    async def update_replicas(self, request):
        if self.local_ip != self.primary:
            msg = await request.json()
            if type(msg) == dict:
                txt = msg
            else:
                txt= json.loads(msg)
            newList = txt["Replica_List"]
            for i in newList:
                if i not in self.all_replicas:
                    self.all_replicas.append(i)
                if i not in self.other_replicas and i != self.local_ip:
                    self.other_replicas.append(i)
            if txt['N_Commit'] > self.n_commit or txt['N_Operation'] > self.n_operation or txt['N_View'] > self.n_view:
                await self.start_recovery()

            #start the heartbeat expectiation from the primary.
            self.timer = Timer(800000, self.send_view_change, self.loop)
            self.timer.start(800000, self.send_view_change)
            return web.Response()
        else: 
            return web.Response(status = 400)

    # This starts the http server and listens for the specified http requests
    async def http_server_start(self):
        self.session = aiohttp.ClientSession()
        self.app = web.Application()
        # add routes that we will need for this system with the corresponding coroutines
        self.app.add_routes([web.post('/PlayerMovement', self.player_move),
                            web.post('/ClientJoin', self.client_join),
                            web.post('/Ready', self.readied_up),
                            
                            web.post("/ReadyConfirm", self.ready_confirm),
                            web.post('/StartConfirm', self.start_confirm),
                            web.post('/StartViewChange', self.start_view_change),
                            web.post('/DoViewChange', self.do_view_change),
                            web.post('/StartView', self.start_view),
                            web.post('/Recover', self.recovery_help),
                            web.post('/RecoveryResponse', self.recovery_response),
                            web.post('/GetState', self.get_state),
                            web.post('/Commit', self.apply_commit),
                            web.post('/PlayerMoveOK', self.player_move_ok),
                            web.post('/GetReplicaList', self.replica_list),
                            web.post('/UpdateReplicaList', self.update_replicas),
                            web.post('/ComputeGamestate', self.compute_gamestate),
                            web.post('/Gamestate', self.receive_gamestate)])
        self.runner = aiohttp.web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.local_ip, 9999)
        await self.site.start()


