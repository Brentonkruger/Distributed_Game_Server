from enum import Enum
import ipaddress
import asyncio
import socket
import secrets
import json
import requests
from aiohttp import web
import aiohttp

class Mode(Enum):
    BACKUP = 0
    PRIMARY = 1

class State(Enum):
    NORMAL = 0
    VIEW_CHANGE = 1
    RECOVERING = 2

class Host():

    def __init__(self, ip_addr):
        self.address = ipaddress.ip_address(ip_addr) 
    
    def get_address(self):
        return self.address
    
    def __str__(self):
        return str(self.address)

    def __lt__(self, other):
        return self.address < other.address



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
        


        self.session = aiohttp.ClientSession()
        self.loop = asyncio.get_event_loop()
        self.app = web.Application()
        
        

        self.loop.create_task(self.http_server_start())
        self.loop.create_task(self.request_primary_ip())

        try:
            self.loop.run_forever()
        except:
            self.loop.close()
        

        

    def find_replicas(self):
        #TODO: 1. Send broadcast to network
        #
        pass

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
    
    #add a new replica with the ip address in form "xxx.xxx.xxx.xxx"
    async def add_new_replica(self, ip_addr):
        if Host(ip_addr) not in self.connected_hosts:
            self.connected_hosts.append(Host(ip_addr))

    #sending message section
    # async def add_to_send_queue(self, ipaddr, msg):
    #     await self.message_out_queue.put((str(ipaddr), msg))
    #     await asyncio.sleep(0)

    async def replica_broadcast(self, msg):
        for rep in self.connected_hosts:
            self.message_out_queue.put((rep.get_address(), msg))

    async def request_primary_ip(self):
        resp = await self.session.get("http://" + self.routing_layer + ":5000/join")
        txt = await resp.text()
        a_resp = json.loads(txt)
        await self.add_new_replica(a_resp['Primary_IP'])
        for i in self.connected_hosts:
            print(i)
        
        
    async def send_message(self, ip_addr, req_type, req_location, data):
        if req_type == "post":
            await self.session.post("http://" + ip_addr + ":9999/" + req_location, data = json.dumps(data))
        if req_type == "get":
            await self.session.get("http://" + ip_addr + ":9999/" + req_location, data = json.dumps(data))
        # while True:
        #     ipaddr, msg = await self.message_out_queue.get()
        #     reader, writer = await asyncio.open_connection(ipaddr, 9998)
        #     print(ipaddr)
        #     # print(msg)
        #     writer.write(msg.encode())
        #     writer.write_eof()
        #     await writer.drain()

    #reading message section
    # async def parse_message(self, reader, writer):
    #     text = ""
    #     # msg = await reader.read()
    #     # text = msg.decode()
    #     # print(text)
    #     msg = await reader.readline()
    #     while(msg != b'\r\n'):
    #         print(msg)
    #         text += msg.decode()
    #         msg = await reader.readline()
        
    #     #from the routing layer
    #     if "HTTP" in text:
    #         lines = text.split('\n')
    #         message_type = lines[0].split(' ')[1].strip('/').split('.')[0]
    #         writer.write(b'HTTP/1.1 200 OK\r\nKeep-alive: ')
    #         writer.write_eof()
    #         print(message_type)
    #         # r = requests.get("http://192.168.0.10:5000/join")
    #         # r = requests.get("http://127.0.0.1:5000/join")
        
    #     #from other servers
    #     #decode json


        # await self.message_out_queue.put(("192.168.0.10", msg.decode()))


    async def http_server_start(self):
        self.app.add_routes([web.get('/JoinOK', self.add_new_replica)])
        self.runner = aiohttp.web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.local_ip, 9999)
        await self.site.start()

    # async def read_network(self):

    #     #open socket and wait for connection
    #     a_server = await asyncio.start_server(self.parse_message, port=9999, start_serving = True)
        
    def createJson(self, type_message):
        #Create a dictionary of the things you want in the json object, then encode.
        # json_dict = {type:}
        pass

    # def create_message(self, type_message, ip_addr, port):
    #     a_string = "HEAD /" + str(type_message) + " HTTP/1.1\nHost: " + ip_addr + ":" + str(port) + "\nAccept-Encoding: identity\nContent-Length: 0"
    #     return a_string

        



