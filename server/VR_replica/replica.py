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

class replica:
    
    def __init__(self, routing_ip):
        self.current_mode = Mode.BACKUP
        self.current_state = State.NORMAL
        self.other_replicas = []
        self.all_replicas = []
        self.message_out_queue = asyncio.Queue()
        self.routing_layer = routing_ip

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
        


    async def start_recovery(self, request):
        self.current_state = State.RECOVERING
        #TODO: run the recovery protocol
        #Send broadcast to all replicas with random nonce 
        nonce = secrets.randbits(32)
        # self.replica_broadcast()

        #Update state from responses until majority is recieved
        self.current_state = State.NORMAL
    
    async def replica_broadcast(self, req_type, req_location, msg):
        for rep in self.other_replicas:
            await self.send_message(str(rep),req_type, req_location, msg)

    async def request_primary_ip(self):
        resp = await self.session.get("http://" + self.routing_layer + ":5000/join")
        txt = await resp.text()
        a_resp = json.loads(txt)
        self.primary = a_resp['Primary_IP']
        if a_resp['Primary_IP'] != self.local_ip:
            self.other_replicas.append(a_resp['Primary_IP'])
            self.all_replicas.append(a_resp['Primary_IP'])
            #connect to primary and ask for updated replica list
            body = {"Type": "GetReplicaList", "IP": self.local_ip}
            await self.send_message(self.primary, "get", "GetReplicaList", json.dumps(body))
        
    async def send_message(self, ip_addr, req_type, req_location, data):
        if req_type == "post":
            await self.session.post("http://" + ip_addr + ":9999/" + req_location, data = json.dumps(data))
        if req_type == "get":
            await self.session.get("http://" + ip_addr + ":9999/" + req_location, data = json.dumps(data))
            
    async def start_view_change(self, request):
        self.current_state = State.VIEW_CHANGE
        #TODO: run the view change protocol
        self.current_state = State.NORMAL

    async def player_move(self, request):
        pass
    async def client_join(self, request):
        pass
    async def start_game(self, request):
        pass
    async def compute_gamestate(self, request):
        pass
    async def do_view_change(self, request):
        pass
    async def readied_up(self, request):
        pass
    async def apply_commit(self, request):
        pass
    async def start_view(self, request):
        pass
    async def get_state(self, request):
        pass
    async def recovery_help(self, request):
        pass
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
            await self.replica_broadcast("post", "UpdateReplicaList", body)
            return web.Response()
        else: 
            return web.Response(status = 400, body = json.dumps({"Primary_IP": self.primary}))

    async def update_replicas(self, request):
        body = await request.json()
        body = json.loads(body)
        newList = body["Replica_List"]
        for i in newList:
            if i not in self.all_replicas:
                self.all_replicas.append(i)
            if i not in self.other_replicas and i != self.local_ip:
                self.other_replicas.append(i)
        return web.Response()

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


