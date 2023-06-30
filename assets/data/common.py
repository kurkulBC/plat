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

    @staticmethod
    def opposite(direction):
        return DirectionTools.opposite(direction)

    @staticmethod
    def rotate(direction):
        return DirectionTools.rotate(direction)


class DirectionTools(object):
    opposites = {
        Direction.up: Direction.down,
        Direction.left: Direction.right,
        Direction.down: Direction.up,
        Direction.right: Direction.left,

        Direction.upleft: Direction.downright,
        Direction.downleft: Direction.upright,
        Direction.downright: Direction.upleft,
        Direction.upright: Direction.downleft,
    }
    rotations = {
        Direction.up: Direction.left,
        Direction.left: Direction.down,
        Direction.down: Direction.right,
        Direction.right: Direction.up,

        Direction.upleft: Direction.downleft,
        Direction.downleft: Direction.downright,
        Direction.downright: Direction.upright,
        Direction.upright: Direction.upleft,
    }

    @staticmethod
    def opposite(direction: Direction):
        try:
            return DirectionTools.opposites[direction]
        except KeyError:
            raise TypeError("Not a Direction")

    @staticmethod
    def rotate(direction: Direction):
        try:
            return DirectionTools.rotations[direction]
        except KeyError:
            return TypeError("Not a Direction")


# dummy class
class Demo(pygame.sprite.Sprite):
    def __init__(self, rect: pygame.rect.Rect | pygame.rect.FRect):
        super().__init__()
        self.rect = rect
