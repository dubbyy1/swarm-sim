from enum import Enum

class Formation(Enum):
    LINE = 1
    CIRCLE = 2
    SQUARE = 3
    TRIANGLE = 4

class State(Enum):
    IDLE = 1
    IN_FORMATION = 2
    EXCLUDED = 3

class Intent(Enum):
    JOIN_NETWORK = 1
    JOIN_FORMATION = 2
    LEAVE_FORMATION = 3,

    SET_FORMATION = 4
    SET_FORMATION_ORDER = 5

class Status(Enum):
    OK = 1
    INCOMPLETE_DATA = 2
