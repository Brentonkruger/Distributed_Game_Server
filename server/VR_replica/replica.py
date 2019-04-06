from enum import Enum
import ipaddress
import asyncio
import socket
import secrets
import json
from aiohttp import web
import aiohttp

class Mode(Enum):
    BACKUP = 0
    PRIMARY = 1

class State(Enum):
    NORMAL = 0
    VIEW_CHANGE = 1
    RECOVERING = 2
    
class Timer:
    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

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
        self._task = asyncio.ensure_future(self._job())

    
    def restart(self):
        self._task.cancel()
        self.task = asyncio.ensure_future(self._job())

class replica:
    
    def __init__(self, routing_ip):
        self.current_mode = Mode.BACKUP
        self.current_state = State.NORMAL
        self.other_replicas = []
        self.all_replicas = []
        self.message_out_queue = asyncio.Queue()
        self.routing_layer = routing_ip
        self.n_view = 0
        self.n_commit = 0
        self.n_operation = 0
        #The log will be a list of the events that have occurred, the lookup will correspond to the Operation number of the request being served
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
        except:
            self.loop.close()
        


		# WORKING HERE
    async def start_recovery(self, request):
        #stop timer running
        self.current_state = State.RECOVERING
		
        #Send broadcast to all replicas with random nonce and its address
        nonce = secrets.randbits(32)
        message = {
            "Type": "Recover",
            "N_replica": self.local_ip,
            "Nonce": nonce
	    }
		
        self.replica_broadcast("post", "Recover", message)
		
		# Waiting until enough responses received
        i = 0
        while i < (len(self.other_replicas) / 2) + 1:
            for rep in self.other_replicas:
                reply = await self.send_message(str(rep), "get", "RecoverResponse", None)
                response = await reply.text()
                update = json.loads(response)
                # Save state information if response is from primary
                if update["N_replica"] == self.primary:
		            #TODO update state of replica
                    pass
                i += 1
		
        #Update state from responses once majority is received
        self.current_state = State.NORMAL

		# WORKING ON ABOVE

    

    async def start_view_change(self, request):
        self.current_state = State.VIEW_CHANGE
        #TODO: run the view change protocol
        self.current_state = State.NORMAL

    
    async def send_view_change(self):
        #change to view change mode
        #send out view change message
        print("timer expired")
        # TODO: implement
        pass

    async def send_commit(self):
        #send out the commit message as a heartbeat
        self.timer.cancel()
        msg = json.dumps({"Type": "Commit", "N_View": self.n_view, "N_Commit": self.n_commit})
        resp = await self.replica_broadcast("post", "Commit", msg)
        self.timer.start()

    async def replica_broadcast(self, req_type, req_location, msg):
        a_status = 200
        for rep in self.other_replicas:
            resp = await self.send_message(str(rep),req_type, req_location, msg)
            if resp.status != 200:
                a_status = resp.status
        return a_status

    async def request_primary_ip(self):
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

            #start the heartbeat expectiation from the primary.
            self.timer = Timer(10, self.send_view_change)
        else:
            #start a timer to send out a commit message (basically as a heartbeat)
            self.timer = Timer(7, self.send_commit)
        
    # Will replace send_message eventually
    async def add_to_message_queue(self, ip_addr, data):
        pass
        await self.message_out_queue.put(data)
        await asyncio.sleep(0)

    async def send_message(self, ip_addr, req_type, req_location, data):
        if req_type == "post":
            await self.session.post("http://" + ip_addr + ":9999/" + req_location, data = json.dumps(data))
        if req_type == "get":
            await self.session.get("http://" + ip_addr + ":9999/" + req_location, data = json.dumps(data))
            

    async def player_move(self, request):
        #check if the move has already been made (op number)
        #primary sends out player move to backups, they add into the gamestate
        if self.local_ip == self.primary:
            msg = await request.json()
            # add fields needed for the replicas (commit number op number etc.)
            resp = await self.replica_broadcast("post", "PlayerMovement", msg)
            #TODO:apply update
            
            #update commit number
            return web.Response()


        #backups recieve the player move and adds it to the gamestate, then replies when it's finished
        else:
            #TODO:apply update
            #update operation number
            #update commit number
            return web.Response()

    async def client_join(self, request):
        #client has joined up
        #TODO: implement
        pass

    async def start_game(self, request):
        #finalize the servers on game start
        #send the message to the clients to begin the game
        #TODO: implement
        pass

    async def compute_gamestate(self, request):
        #compute gamestate and return message
        #TODO: implement
        pass

    async def do_view_change(self, request):
        #send the doviewchange message
        #{
        #     "Type": "DoViewChange",
        #     "N_View": 1,
        #     "Log": "Log things",
        #     "N_View_Old": 0,
        #     "N_Operation": 16,
        #     "N_Commit": 15,
        #     "N_replica": 2
        # }
        #TODO: implement
        pass

    async def readied_up(self, request):
        #add the user's ready state
        #TODO: implement
        pass

    async def apply_commit(self, request):
        #recieve the commit message, and apply if necessary.
        self.timer.cancel()
        msg = await request.json()
        text = json.loads(msg)
        if text["N_View"] > self.n_view:
            #go into recovery mode
            # TODO: implement
            pass
        elif text["n_commit"] > self.n_commit:
            #go into state transfer mode
            # TODO: implement
            pass
        else:  
            return web.Response()
            
        self.timer.start()
        #don't update client about this one.

    async def start_view(self, request):
        #recieve the new view message to begin the next view
        #TODO: implement
        return web.Request()
        

    async def get_state(self, request):
        msg = json.dumps({"Type": "NewState","N_View":self.n_view,"Log":self.log[-1],"N_Operation":self.n_operation,"N_Commit":self.n_commit})
        return web.Response(body = msg)

    async def recovery_help(self, request):
        #send back the recover message
        if self.primary == self.local_ip:
            #return the intense answer
            body = request.json()
            txt = json.loads(body)
            nonce = txt['Nonce']
            reply = json.dumps({
                "Type": "RecoverResponse",
                "N_View": self.n_view,
                "Nonce": nonce,
                "Log": self.log,
                "N_Operation": self.n_operation,
                "N_Commit": self.n_commit
            })
            return web.Response(body = reply)
        else:
            #return the small answer
            body = await request.json()
            text = json.loads(body)
            msg = json.dumps({"Type": "RecoveryResponse","N_View":self.n_view,"Nonce":text['Nonce'],"Log":"Nil","N_Operation":"Nil","N_Commit":"Nil"})
            return web.Response(body = msg)
         
        

    async def replica_list(self, request):
        #format the replica list and return it to the backup
        if self.local_ip == self.primary:
            if request.remote != self.local_ip:
                if request.remote not in self.all_replicas:
                    self.all_replicas.append(request.remote)
                    print("Added\t" + request.remote)
                if request.remote not in self.other_replicas:
                    self.other_replicas.append(request.remote)

            body = json.dumps({"Type": "UpdateReplicaList", "Replica_List": [i for i in self.all_replicas]})
            resp = await self.replica_broadcast("post", "UpdateReplicaList", body)
            return web.Response()
        else: 
            return web.Response(status = 400, body = json.dumps({"Primary_IP": self.primary}))

    async def update_replicas(self, request):
        if self.local_ip == self.primary:
            body = await request.json()
            body = json.loads(body)
            newList = body["Replica_List"]
            for i in newList:
                if i not in self.all_replicas:
                    self.all_replicas.append(i)
                if i not in self.other_replicas and i != self.local_ip:
                    self.other_replicas.append(i)
            return web.Response()
        else: 
            return web.Response(status = 400, body = json.dumps({"Primary_IP": self.primary}))

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
                            web.post('/GetState', self.get_state),
                            web.post('/Commit', self.apply_commit),
                            web.get('/GetReplicaList', self.replica_list),
                            web.post('/UpdateReplicaList', self.update_replicas),
                            web.get('/ComputeGamestate', self.compute_gamestate)])
        self.runner = aiohttp.web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.local_ip, 9999)
        await self.site.start()


