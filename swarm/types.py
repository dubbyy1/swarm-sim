from enum import Enum

class Formation(Enum):
    LINE = 1
    CIRCLE = 2
    IDLE = 3

class State(Enum):
    IDLE = 1
    IN_FORMATION = 2
    EXCLUDED = 3
    REMOTE = 4

class Intent(Enum):
    JOIN_NETWORK = 1
    JOIN_FORMATION = 2
    LEAVE_FORMATION = 3,

    SET_FORMATION = 4
    SET_FORMATION_ORDER = 5
