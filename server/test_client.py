 
import asyncio
from asyncio import StreamReader, StreamWriter
import ipaddress
import requests
from http import client as httpclient
import json
import aiohttp


class Message:
    def __init__(self, opp_num, msg_body):
        self.recieved_backups = {}
        self.operation_number = opp_num
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


async def client():


    ## aiohttp ##
    async with aiohttp.ClientSession() as session:

        op_num = 0
        log = {}
        msg = Message(0,"BODY")


        async with session.get('http://192.168.0.10:9999/get') as resp:
            print(resp.status)
            print(await resp.text())


    


asyncio.run(client())
# client()