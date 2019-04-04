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
        self.connected_hosts = []
        self.message_out_queue = asyncio.Queue()
        self.routing_layer = routing_ip

        #get Ip of the local computer
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        #s.getsockname() has the local ip address at [0] and the local port at [1]
        self.local_ip = s.getsockname()[0]
        print("IP address: ", self.local_ip)
        s.close()
        

        #start the local loop to allow for asyncio (starts the server)       
        self.loop = asyncio.get_event_loop()

        self.loop.create_task(self.http_server_start())
        self.loop.create_task(self.request_primary_ip())

        try:
            self.loop.run_forever()
        except:
            self.loop.close()
        


    def start_recovery(self):
        self.current_state = State.RECOVERING
        #TODO: run the recovery protocol
        #Send broadcast to all replicas with random nonce 
        nonce = secrets.randbits(32)
        # self.replica_broadcast()

        #Update state from responses until majority is recieved
        self.current_state = State.NORMAL

    def start_view_change(self):
        self.current_state = State.VIEW_CHANGE
        #TODO: run the view change protocol
        self.current_state = State.NORMAL
    
    def host_list_to_json(self):
        hosts = {"Type": "Replica_List", "Replica_List":self.connected_hosts}
        return json.dumps(hosts)
    
    #add a new replica with the ip address in form "xxx.xxx.xxx.xxx"
    async def add_new_replica(self, ip_addr):
        if ip_addr not in self.connected_hosts:
            self.connected_hosts.append(ip_addr)
            await self.replica_broadcast("post", "UpdateReplicaList", self.host_list_to_json())

    async def process_request(self):
        pass
        

    #sending message section

    async def send_replica_list(self, request):
        print(request)
        pass

    async def replica_broadcast(self, req_type, req_location, msg):
        for rep in self.connected_hosts:
            await self.send_message(str(rep),req_type, req_location, msg)

    async def request_primary_ip(self):
        #add local ip
        # await self.add_new_replica(self.local_ip)
        #request primary ip
        resp = await self.session.get("http://" + self.routing_layer + ":5000/join")
        txt = await resp.text()
        a_resp = json.loads(txt)
        if a_resp['Primary_IP'] != self.local_ip:
            await self.add_new_replica(a_resp['Primary_IP'])
        self.primary = a_resp['Primary_IP']
        
        
        
    async def send_message(self, ip_addr, req_type, req_location, data):
        if req_type == "post":
            await self.session.post("http://" + ip_addr + ":9999/" + req_location, data = json.dumps(data))
        if req_type == "get":
            await self.session.get("http://" + ip_addr + ":9999/" + req_location, data = json.dumps(data))



    async def http_server_start(self):
        self.session = aiohttp.ClientSession()
        self.app = web.Application()
        self.app.add_routes([web.get('/JoinOK', self.add_new_replica),
                            web.post('/Request', self.process_request),
                            web.post('/ViewChange', self.start_view_change),
                            web.post('/Ready', self.readied_up),
                            web.post('/Recover', self.start_recovery),
                            web.post('/Commit', self.apply_commit),
                            web.post('/UpdateReplicaList', self.send_replica_list)])
        self.runner = aiohttp.web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.local_ip, 9999)
        await self.site.start()

    
        
    
