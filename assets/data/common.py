from enum import Enum, unique, auto
import pygame.sprite

screenwidth = 1072
screenheight = 1072
width = 1024
height = 1024
size = 32


@unique
class Direction(Enum):
    up = auto()
    left = auto()
    down = auto()
    right = auto()

    upleft = auto()
    downleft = auto()
    downright = auto()
    upright = auto()

    opposites = {
        up: down,
        left: right,
        down: up,
        right: left,

        upleft: downright,
        downleft: upright,
        downright: upleft,
        upright: downleft,
    }
    rotations = {
        up: left,
        left: down,
        down: right,
        right: up,

        upleft: downleft,
        downleft: downright,
        downright: upright,
        upright: upleft,
    }

    @staticmethod
    def opposite(direction):
        try:
            return Direction.opposites[direction]
        except KeyError:
            raise TypeError("Not a Direction")

    @staticmethod
    def rotate(direction):
        try:
            return Direction.rotations[direction]
        except KeyError:
            return TypeError("Not a Direction")


# dummy class
class Demo(pygame.sprite.Sprite):
    def __init__(self, rect: pygame.rect.Rect | pygame.rect.FRect):
        super().__init__()
        self.rect = rect
