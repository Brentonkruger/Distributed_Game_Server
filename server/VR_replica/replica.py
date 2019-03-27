from enum import Enum
import ipaddress

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

    def __lt__(self, other):
        return self.address < other.address


class replica:
    
    def __init__(self):
        self.current_mode = Mode.BACKUP
        self.current_state = State.NORMAL
        self.connected_hosts = []

    def start_recovery(self):
        self.current_state = State.RECOVERING
        #TODO: run the recovery protocol.
        self.current_state = State.NORMAL

    def start_view_change(self):
        self.current_state = State.VIEW_CHANGE
        #TODO: run the view change protocol
        self.current_state = State.NORMAL
    
    #add a new replica with the ip address in form "xxx.xxx.xxx.xxx"
    def add_new_replica(self, ip_addr):
        self.connected_hosts.append(Host(ip_addr))
