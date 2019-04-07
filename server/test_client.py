 
import asyncio
from asyncio import StreamReader, StreamWriter
import ipaddress
import requests
from http import client as httpclient
import json
import aiohttp



async def client():

    ## requests module ##
    # r = requests.post('http://192.168.0.10:9999/resource', json = json.dumps('{"Type": "Request","Operation": ["Up","Down","Left","Right"],"Client_ID": 2,"N_Request": 5}'))

    ## native python ##
    # a_client = httpclient.HTTPConnection('192.168.0.10', 9999)
    # a_client.request("POST", "/gamestate", body = json.dumps('{"Type": "Request","Operation": ["U","D","L","R","N"],"Client_ID": 2,"N_Request": 5}'))
    # data = a_client.getresponse()

    ## aiohttp ##
    async with aiohttp.ClientSession() as session:
        async with session.get('http://192.168.0.10:9999/get') as resp:
            print(resp.status)
            print(await resp.text())


    

#     reader, writer = await asyncio.open_connection(str(ipaddress.ip_address('192.168.0.10')), 9999)
#     # reader, writer = await asyncio.open_connection('192.168.1.89', 9999)
#     writer.write("Message from client".encode())
#     await writer.drain()

asyncio.run(client())
# client()