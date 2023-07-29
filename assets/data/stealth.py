import pygame
from common import Direction, Demo


class Guard(pygame.sprite.Sprite):
    awareness = {
        'observing': pygame.image.load("../img/stealth/eye.png"),
        'cautious': pygame.image.load("../img/stealth/questionmark.png"),
        'alert': pygame.image.load("../img/stealth/exclamationmark.png"),
    }

    def __init__(self, x, y, image="../imgx/stealth/guard.png", facing=Direction.left, speed=None, path=None):
        super().__init__()
        self.x = x
        self.y = y
        self.imageL = pygame.image.load(image)
        self.imageR = pygame.transform.flip(self.imageL, False, True)
        self.rect = self.imageL.get_rect()
        self.rect.x, self.rect.y = x, y
        self.facing = facing
        self.speed = speed
        if speed is None:
            self.speed = [2, 5]
        self.path = path
        if path is not None:
            self.path = [Demo(pygame.rect.Rect(*s, 1, 1)) for s in path]
        self.alert = 0.0
        self.lastpathpos = None
