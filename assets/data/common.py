from enum import Enum, unique, auto

@unique
class Direction(Enum):
    up = auto()
    left = auto()
    down = auto()
    right = auto()