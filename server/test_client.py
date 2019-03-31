 
import asyncio
from asyncio import StreamReader, StreamWriter
import ipaddress



async def client():
    reader, writer = await asyncio.open_connection(ipaddress.ip_address('192.168.0.10'), 9999)
    # reader, writer = await asyncio.open_connection('192.168.1.89', 9999)
    writer.write("Message from client".encode())
    await writer.drain()

asyncio.run(client())