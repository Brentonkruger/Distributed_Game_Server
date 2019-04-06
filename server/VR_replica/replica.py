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
        


		# WORKING HERE
    async def start_recovery(self, request):
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
        while i < (len(self.connected_hosts) / 2) + 1:
            for rep in self.connected_hosts:
                reply = await self.send_message(str(rep), "get", "RecoverResponse", None)
                response = await reply.text()
                update = json.loads(response)
                # Save state information if response is from primary
                if update["N_replica"] == self.request_primary_ip():
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
    
    def host_list_to_json(self):
        hosts = {"Type": "Replica_List", "Replica_List":self.connected_hosts}
        return json.dumps(hosts)
    
    #add a new replica with the ip address in form "xxx.xxx.xxx.xxx"
    async def add_new_replica(self, ip_addr):
        if ip_addr not in self.connected_hosts:
            self.connected_hosts.append(ip_addr)
            await self.replica_broadcast("post", "UpdateReplicaList", self.host_list_to_json())

    
        

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

    async def process_request(self, request):
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
        info = json.loads(request.json())
        nonce = info["Nonce"]
        crashed_replica = info["N_replica"]

        # Response
        # If replica is the primary, send everything
        if self.primary == self.local_ip:
            reply = {
                "Type": "RecoverResponse",
                #"N_View": /* View Number */,
                "Nonce": nonce,
                #"Log": log,
                #"N_Operation": /* Operation number */,
                #"N_Commit": /* Commit number */,
                "N_replica": self.local_ip
            }
        # If not, send limited information
        else:
            reply = {
                "Type": "RecoverResponse",
                #"N_View": /* View Number */,
                "Crashed_Replica": nonce,
                "Log": None,
                "N_Operation": None,
                "N_Commit": None,
                "N_replica": self.local_ip
            }

        # Send reply back to crashed replica
        # Replace once send_message is removed
        self.send_message(self.local_ip, "post", "RecoverResponse", reply)


    # This starts the http server and listens for the specified http requests
    async def http_server_start(self):
        self.session = aiohttp.ClientSession()
        self.app = web.Application()
        # add routes that we will need for this system with the corresponding coroutines
        self.app.add_routes([web.post('/PlayerMovement', self.process_request),
                            web.post('/ClientJoin', self.client_join),
                            web.post('/Ready', self.readied_up),

                            web.post('/StartViewChange', self.start_view_change),
                            web.post('/DoViewChange', self.do_view_change),
                            web.post('/StartView', self.start_view),
                            web.post('/Recover', self.recovery_help),
                            web.post('/GetState', self.get_state),
                            web.post('/Commit', self.apply_commit),
                            web.get('/ComputeGamestate', self.compute_gamestate)])
        self.runner = aiohttp.web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.local_ip, 9999)
        await self.site.start()


