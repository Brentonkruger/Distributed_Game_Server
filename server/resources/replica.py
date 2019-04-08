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

class Mode(Enum):
    BACKUP = 0
    PRIMARY = 1

class State(Enum):
    NORMAL = 0
    VIEW_CHANGE = 1
    RECOVERING = 2
    
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
        self.current_mode = Mode.BACKUP
        self.current_state = State.NORMAL
        self.other_replicas = []
        self.all_replicas = []
        self.ready_up = []
        self.client_list = {}
        self.client_requests = list(list())
        self.request_ok = []
        self.message_out_queue = asyncio.Queue()
        self.routing_layer = routing_ip
        self.n_view = 0
        self.n_commit = 0
        self.n_operation = 0
        self.n_recovery_messages = 0
        self.n_start_view_change_messages = 0
        self.n_do_view_change_messages = 0
        self.n_gamestate_responses = 0
        self.start_view_change_sent = False
        self.primary_recovery_response = False
        self.game_running = False
        self.current_turn = 0
        self.request_gamestate_update = False
        self.log = []

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

        self.timer.cancel()
        #Send broadcast to all replicas with random nonce and its address
        self.recovery_nonce = secrets.randbits(32)
        message = json.dumps({
            "Type": "Recover",
            "N_replica": self.local_ip,
            "Nonce": self.recovery_nonce
	    })
        self.replica_broadcast("post", "Recover", message)

    async def recovery_response(self, request):
        if self.current_state == State.RECOVERING:
            body = await request.json()
            txt = json.loads(body)
            if txt["Nonce"] == self.recovery_nonce:
                self.n_recovery_messages +=1
                if request.remote == self.primary:
                    # save state info
                    self.log = txt["Log"]###we will need to sort this log bit out
                    self.n_commit = txt["N_Commit"]
                    self.n_operation = txt["N_Operation"]
                    self.n_view = txt["N_View"]
                    self.primary_recovery_response = True
                if self.n_recovery_messages >= int(len(self.other_replicas)/2) and self.primary_recovery_response:
                    self.n_recovery_messages = 0
                    self.primary_recovery_response = False
                    self.current_state = State.NORMAL
                    self.timer.start()
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
        reply = await request.json()
        txt = json.loads(reply)

        if self.n_view >= txt["N_View"]:
            if not self.start_view_change_sent:
                message = json.dumps({
                    "N_View": self.n_view,
                    "N_replica": self.local_ip})
                self.replica_broadcast("post", "StartViewChange", message)
                self.start_view_change_sent = True
            self.n_start_view_change_messages += 1
            
        if self.n_start_view_change_messages >= int(len(self.other_replicas)/2):
            msg = json.dumps({
                "Type": "DoViewChange",
                "N_View": self.n_view,
                "Log": [i for i in self.log],
                "N_View_Old": self.n_view-1,
                "N_Operation": self.n_operation,
                "N_Commit": self.n_commit,
                "N_replica": self.local_ip
                })
            # Send DoViewChange to new primary
            self.primary = self.get_new_primary_replica(self.primary)
            self.send_message(self.primary, "post", "DoViewChange", msg)
        return web.Response()

    async def send_view_change(self):
        #change to view change mode
        #send out initial view change message
        self.current_state = State.VIEW_CHANGE
        self.n_view += 1
        message = json.dumps({
            "N_View": self.n_view,
            "N_replica": self.local_ip})
        self.replica_broadcast("post", "StartViewChange", message)
        self.start_view_change_sent = True


    async def do_view_change(self, request):
        # If replica is primary, wait for f + 1 DoViewChange responses and update information
        if self.primary == self.local_ip:
            reply = await request.json()
            txt = reply.loads(reply)
            #update the primary if behind 
            if self.n_view <= txt["N_View"]:
                if self.n_operation < txt["N_Operation"]:
                    self.log = txt["Log"]
                    self.n_operation = txt["N_Operation"]
                    self.n_commit = txt["N_Commit"]

            if self.n_do_view_change_messages >= int(len(self.all_replicas) / 2):
                # Change status back to normal and send startview message to other replicas
                self.current_state = State.NORMAL
                # StartView json
                startview_message = json.dumps({
                    "Type": "StartView",
                    "N_View": self.n_view,
                    "Log": self.log,
                    "N_Operation": self.n_operation,
                    "N_Commit": self.n_commit
                })

                # Broadcast message to other replicas
                self.replica_broadcast("post", "StartView", startview_message)
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
        resp = await self.session.get("http://" + self.routing_layer + ":5000/join")
        txt = await resp.text()
        a_resp = json.loads(txt)
        self.primary = a_resp['Primary_IP']
        if a_resp['Primary_IP'] != self.local_ip:
            self.other_replicas.append(a_resp['Primary_IP'])
            self.all_replicas.append(a_resp['Primary_IP'])

            #connect to primary and ask for updated replica list
            msg = json.dumps({"Type": "GetReplicaList", "IP": self.local_ip})
            await self.send_message(self.primary, "get", "GetReplicaList", msg)
            
        else:
            #start a timer to send out a commit message (basically as a heartbeat)
            self.timer = Timer(7, self.send_commit, self.loop)
            self.timer.start(7, self.send_commit)

    async def get_new_primary_replica(self, old_ip):
        index = self.all_replicas.index(old_ip)
        return self.all_replicas[(index + 1) % len(self.all_replicas)]
        

    async def send_message(self, ip_addr, req_type, req_location, data):
        if req_type == "post":
            await self.session.post("http://" + ip_addr + ":9999/" + req_location, data = json.dumps(data))
        if req_type == "get":
            await self.session.get("http://" + ip_addr + ":9999/" + req_location, data = json.dumps(data))
            

    async def player_move(self, request):
        #check if the move has already been made (op number)
        #TODO: stop timer and reset
        msg = await request.json()
        if type(msg) == dict:
            text = msg
        else:
            text = json.loads(msg)
        #primary sends out player move to backups, they add into the gamestate
        if self.local_ip == self.primary:
            op_id = self.client_requests[text['Client_ID']][text['Client_ID']]
            if op_id <= self.n_commit:
                msg = json.dumps({
                    "Type": "GameUpdate",
                    "Gamestate": self.log[op_id]
                })
                return web.Response(body = msg)
                
            else:
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
                await self.replica_broadcast("post", "PlayerMovement", msg)              

                return web.Response()
        
        #backups receive the player move and adds it to the gamestate, then replies when it's finished
        else:
            #TODO:apply update to gamestate
            if text["N_Operation"] > self.n_operation:
                self.n_operation = text["N_Operation"]
            if text["N_Commit"] > self.n_commit:
                self.n_commit = text["N_Commit"]
            if test["N_View"] > self.n_view:
                self.start_state_transfer()
            turnjson = self.game_board.complete_turn()

            #update operation number
            #update commit number
            #if view number is different, go to state transfer mode

            return web.Response()
    
    async def player_move_ok(self, request):
        #TODO: implement
        msg = await request.json()
        if type(msg) == dict:
            text = msg
        else:
            text = json.loads(msg)
        if self.local_ip == self.primary:
            self.request_ok[text['N_Operation']] += 1
            if self.request_ok[text['N_Operation']] > (len(self.client_list)/2):
                #request has quorum.
                #TODO: find out how to give the lowest return numbers without overwriting commit
                #TODO: Run compute gamestate function
                pass
        


    async def client_join(self, request):
        #client has joined up
        #check for a running game
        if not self.game_running:
            if request.remote not in self.client_list:
                self.client_list[request.remote] = len(self.client_list)
                print("added client")
            if self.local_ip == self.primary:
                msg = await request.json()
                if type(msg) == dict:
                    text = msg
                else:
                    text = json.loads(msg)
                resp = json.dumps({
                    "Type": "ClientJoinOK",
                    "Client_ID": self.client_list[request.remote],
                    "N_Request": text['N_Request']})
                return web.Response(body = resp)
            else:
                return web.Response()
        else:
            return web.Response(status = 400)

    async def readied_up(self, request):
        #add the user's ready state

        msg = await request.json()
        if type(msg) == dict:
            text = msg
        else:
            text = json.loads(msg)
        
        cid = text['Client_ID']
        if cid not in self.ready_up:
            self.ready_up.append(cid)
        #primary sends backups request, who respond I guess?
        if self.local_ip == self.primary:
            self.replica_broadcast("post", "Ready", json.dumps(text))
        
        if len(self.ready_up) == len(self.client_list):
            self.start_game()

        

    async def start_game(self):
        #finalize the servers on game start
        #send the message to the clients to begin the game
        self.game_running = True

        ####################### IMPORTANT #######################
        # Current logic is the board is 2x the number of players
        # Change below if we want logic to change
        ####################### IMPORTANT #######################
        size = int(len(self.client_list)) * 2
        self.game_board = board.Board(size)
        gamestate = self.game_board.get_full_gamestate()
        
        start = json.dumps({
            "Type": "GameStart",
            "Gamestate": gamestate
        })
        self.session.post("http://" + self.routing_layer + ":5000/GameStart", data=start)
        self.turn_timer = Timer(7, self.turn_cutoff, self.loop)

    async def turn_cutoff(self):
        pass

    async def compute_gamestate(self, request):
        #compute gamestate and return message
        # If primary, send bad response
        if self.primary == self.local_ip:
            return web.Response(status = 400, body = json.dumps({"Primary_IP": self.primary}))
        # Send response to primary
        else:
            #TODO: update gamestate
            update = json.dumps({
                "Type": "GameState",
                "N_View": self.n_view,
                "N_Operation": self.n_operation,
                "N_Commit": self.n_commit
            })
            self.send_message(self.primary, "post", "GameState", update)
            return web.Response()
    
    async def receive_gamestate(self, request):
        # Only primary should receive gamestate
        if self.primary == self.local_ip:
            update = await request.json()
            gamestate = json.loads(update)
            if gamestate["Type"] == "GameState":
                self.n_gamestate_responses += 1
            # Once enough responses received, send to clients with final gamestate
            if self.n_gamestate_responses > int(len(self.other_replicas) / 2):
                if self.current_turn
                self.turn_timer.cancel()
                #TODO: update gamestate
                #self.log
                new_gamestate = json.dumps({
                    "Type": "GameUpdate",
                    "Gamestate": self.gamestate
                })
                self.session.post("http://" + self.routing_layer + ":5000/GameUpdate", data=new_gamestate)
                self.turn_timer.start()

        # If not primary, send address of primary to replica
        else:
            return web.Response(status = 400, body = json.dumps({"Primary_IP": self.primary}))

    async def apply_commit(self, request):
        #recieve the commit message, and apply if necessary.
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
        body = await request.json()
        txt = json.loads(body)
        self.n_view = txt['N_View']
        self.Log = txt['Log']
        self.n_operation = txt['N_Operation']
        self.n_commit = txt['N_Commit']
        self.primary = request.remote
        self.current_state = State.NORMAL
        return web.Request()
    
    async def start_state_transfer(self):
        #send state transfer
        self.n_operation = self.n_commit
        self.log = self.log[:self.n_operation+1]
        msg = {
            "Type": "GetState",
            "N_View":self.n_view,
            "N_Operation":self.n_operation,
            "N_Replica":self.local_ip
        }
        # self.send_message(self.other_replicas[random.randint(0,len(self.other_replicas))], "get", "GetState", msg)
        tmp_list = self.other_replicas
        # print(random.sample(tmp_list,1))
        resp = await self.send_message(random.sample(tmp_list, 1)[0], "get", "GetState", msg)
        #update state
        txt = json.loads(await resp.text())
        self.n_view = txt['N_View']
        self.n_operation = txt['N_Operation']
        self.n_commit = txt['N_Commit']
        self.log.append(i for i in txt['Log'])

    async def get_state(self, request):
        body = await request.json()
        txt = json.loads(body)

        msg = json.dumps({
            "Type": "NewState",
            "N_View":self.n_view,
            "Log":[i for i in self.log[txt['N_Operation']:]],
            "N_Operation":self.n_operation,
            "N_Commit":self.n_commit})
            
        return web.Response(body = msg)

    async def recovery_help(self, request):
        if self.current_state != State.RECOVERING:        
            #send back the recover message
            body = await request.json()
            txt = json.loads(body)
            if self.primary == self.local_ip:
                #return the intense answer
                reply = json.dumps({
                    "Type": "RecoverResponse",
                    "N_View": self.n_view,
                    "Nonce": txt['Nonce'],
                    "Log": [i for i in self.log],
                    "N_Operation": self.n_operation,
                    "N_Commit": self.n_commit
                })
                self.send_message(request.remote, "post", "RecoveryResponse", reply)
                return web.Response()
            else:
                #return the small answer
                msg = json.dumps({
                    "Type": "RecoveryResponse",
                    "N_View":self.n_view,
                    "Nonce":txt['Nonce'],
                    "Log":"Nil",
                    "N_Operation":"Nil",
                    "N_Commit":"Nil"})
                self.send_message(request.remote, "post", "RecoveryResponse", msg)
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
            body = await request.json()
            txt = json.loads(body)
            newList = txt["Replica_List"]
            for i in newList:
                if i not in self.all_replicas:
                    self.all_replicas.append(i)
                if i not in self.other_replicas and i != self.local_ip:
                    self.other_replicas.append(i)
            if txt['N_Commit'] > self.n_commit or txt['N_Operation'] > self.n_operation or txt['N_View'] > self.n_view:
                self.start_recovery()

            #start the heartbeat expectiation from the primary.
            self.timer = Timer(10, self.send_view_change, self.loop)
            self.timer.start(10, self.send_view_change)
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
                            
                            web.post('/StartViewChange', self.start_view_change),
                            web.post('/DoViewChange', self.do_view_change),
                            web.post('/StartView', self.start_view),
                            web.post('/Recover', self.recovery_help),
                            web.post('/RecoveryResponse', self.recovery_response),
                            web.post('/GetState', self.get_state),
                            web.post('/Commit', self.apply_commit),
                            web.post('/PlayerMoveOK', self.player_move_ok),
                            web.get('/GetReplicaList', self.replica_list),
                            web.post('/UpdateReplicaList', self.update_replicas),
                            web.get('/ComputeGamestate', self.compute_gamestate),
                            web.get('/Gamestate', self.receive_gamestate)])
        self.runner = aiohttp.web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.local_ip, 9999)
        await self.site.start()


