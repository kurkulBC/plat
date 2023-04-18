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


# dummy class
class Demo(pygame.sprite.Sprite):
    def __init__(self, rect: pygame.rect.Rect):
        super().__init__()
        self.rect = rect
