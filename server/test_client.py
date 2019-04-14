 
# import asyncio
# from asyncio import StreamReader, StreamWriter
# import ipaddress
# import requests
# from http import client as httpclient
import json
from json import JSONEncoder
# import aiohttp

class Message():
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

class MessageEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Message):
            return {
            "recieved_backups": obj.recieved_backups,
            "operation_number": obj.operation_number, 
            "msg_body": obj.msg_body, 
            "sent_to_client": obj.sent_to_client}
        return json.JSONEncoder.default(self, obj)



def client():
    op_num = 0
    msg = Message(op_num, "BODY")
    msg.recieve_backup("192.168.2.0")
    print(msg)
    jd = json.dumps(obj = msg, cls = MessageEncoder)
    print(jd)

    newmsg = json.loads(jd)
    print(newmsg)
    # log = {}
    # log[op_num] = msg

    # print(json.dumps(log))
   
    # ## aiohttp ##
    # async with aiohttp.ClientSession() as session:
    #     async with session.get('http://192.168.0.10:9999/get') as resp:
    #         print(resp.status)
    #         print(await resp.text())


    


# asyncio.run(client())
client()