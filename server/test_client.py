 
import asyncio
from asyncio import StreamReader, StreamWriter
import ipaddress
from http import client as httpclient



def client():
    a_client = httpclient.HTTPConnection('192.168.0.10', 9999)
    a_client.request("POST", "/index.html")
    # data = a_client.getresponse()

#     reader, writer = await asyncio.open_connection(str(ipaddress.ip_address('192.168.0.10')), 9999)
#     # reader, writer = await asyncio.open_connection('192.168.1.89', 9999)
#     writer.write("Message from client".encode())
#     await writer.drain()

# asyncio.run(client())
client()