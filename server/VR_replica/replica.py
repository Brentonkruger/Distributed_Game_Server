from enum import Enum

class Mode(Enum):
    BACKUP = 0
    PRIMARY = 1

class State(Enum):
    NORMAL = 0
    VIEW_CHANGE = 1
    RECOVERING = 2



class replica:
    
    def __init__(self):
        self.current_mode = Mode.BACKUP
        self.current_state = State.NORMAL
