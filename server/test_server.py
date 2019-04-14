import asyncio
from http import server
from http.server import SimpleHTTPRequestHandler

class Message:
    def __init__(self, opp_num, msg_body):
        self.recieved_backups = {}
        self.operation_number = opp_num
        self.msg_body = msg_body
        self.sent_to_client = False

<<<<<<< HEAD
class Message:
    def __init__(self, opp_num, msg_body):
        self.recieved_backups = {}
        self.operation_number = opp_num
        self.msg_body = msg_body
        self.sent_to_client = False
=======
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
>>>>>>> 0bd470f48533e41f47e9fbc264991249c6294673

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


def main():
        handler = SimpleHTTPRequestHandler
        a_server = server.HTTPServer(("192.168.0.10", 9998), handler)
        a_server.serve_forever
 

<<<<<<< HEAD
        
=======
>>>>>>> 0bd470f48533e41f47e9fbc264991249c6294673
main()
