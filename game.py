import pygame
import pygame.font as fonts
from assets.data.data import levels as levels
from assets.data.data import leveldescs as leveldescs
from assets.data.data import anims as anims
import assets.data.colors as colors
import assets.hax as hax
from enum import Enum, unique, auto
import random
from glitch_this import ImageGlitcher
from math import floor, ceil
import timeit

invisiblespawn = False

pygame.init()
# hax.active = True
screenwidth = 1072
screenheight = 1072
width = 1024
height = 1024
zoom = 1
animlive = False
screenshake = [0, 0]
shaketime = 0
shakeintensity = [0, 0]
shakedecay = [0, 0]
screenrotation = 0
mute = False
framerate = 60

screen = pygame.display.set_mode((screenwidth, screenheight), pygame.FULLSCREEN | pygame.SCALED)
win = pygame.Surface((screenwidth, screenheight))
tempsurf = pygame.Surface((screenwidth, screenheight), pygame.SRCALPHA)

pygame.display.set_caption("Platman")
pygame.display.set_icon(pygame.image.load("assets/img/platterman.png"))
clock = pygame.time.Clock()
levelx = 0
levely = 0
cutscene = False
cutscenecount = 0
glitcher = ImageGlitcher()
glitchimg = pygame.image.load("assets/img/escape.png")
animtime = 0

# create tile groups
spacetiles = pygame.sprite.Group()
blocktiles = pygame.sprite.Group()
lavatiles = pygame.sprite.Group()
esctiles = pygame.sprite.Group()
elevtiles = pygame.sprite.Group()
circuittiles = pygame.sprite.Group()
switchtiles = pygame.sprite.Group()
doortiles = pygame.sprite.Group()
rocktiles = pygame.sprite.Group()
turrettiles = pygame.sprite.Group()
bullets = pygame.sprite.Group()
lighttiles = pygame.sprite.Group()
lightingtiles = pygame.sprite.Group()
vortextiles = pygame.sprite.Group()
pistontiles = pygame.sprite.Group()
pistonrodtiles = pygame.sprite.Group()

# create special groups
spritesbg = pygame.sprite.Group()
sprites = pygame.sprite.Group()
sprites2 = pygame.sprite.Group()
projectiles = pygame.sprite.Group()

collidetiles = pygame.sprite.Group()
elevcollidetiles = pygame.sprite.Group()
bulletcollidetiles = pygame.sprite.Group()
solidtiles = pygame.sprite.Group()
tiles = pygame.sprite.Group()

# load sound
ost = pygame.mixer.music
crush = pygame.mixer.Sound("assets/sfx/crush.ogg")
melt = pygame.mixer.Sound("assets/sfx/melt.ogg")
shoot = pygame.mixer.Sound("assets/sfx/shoot.ogg")
hit = pygame.mixer.Sound("assets/sfx/hit.ogg")
shotkill = pygame.mixer.Sound("assets/sfx/shotkill.ogg")
press = pygame.mixer.Sound("assets/sfx/press.ogg")
animsound = pygame.mixer.Sound("assets/sfx/anims/anim1glitch.ogg")

# load misc
if hax.active:
    levelcount = hax.startlevel - 2
else:
    levelcount = 2
size = 32
currentlvl = [0]
powered = []
lights = pygame.surface.Surface((1024, 1024))
stealth = False


# define player class
# TODO: fix movement values
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.momentum = 0
        self.baseaccel = 1
        self.airaccel = 0.5
        self.deaccel = 2
        self.acceleration = 0
        self.vel = 10
        self.turnrate = 1.5
        self.transportmomentum = 0
        self.moving = False
        self.alive = True
        self.vertforce = 0
        self.gravity = 1
        self.jumpheight = 20
        self.tvel = 21
        self.jumping = False
        self.minjump = 5
        self.maxjump = self.jumpheight / self.gravity
        self.jumpholding = False
        self.jumptime = 0
        self.jumpsmoothing = 5
        self.jumprelease = 0
        self.grounded = False
        self.escaped = True
        self.image = pygame.image.load("assets/img/platterman.png")
        self.rect = self.image.get_rect()
        self.levelcount = -1
        self.coyotetime = 6
        self.buffertime = 0
        self.buffering = False
        self.wasgrounded = 0
        self.mask = pygame.mask.from_surface(self.image)

    # calculates gravity
    def gravitycalc(self):
        self.buffering = False
        self.rect.y += 2
        grounded = pygame.sprite.spritecollide(self, collidetiles, False)
        if len(grounded) > 0 or self.rect.bottom >= height:
            self.rect.y -= 2
            if not self.grounded:
                self.grounded = True
                if self.wasgrounded > 0 and self.vertforce != 0:
                    self.momentum /= (abs(self.vertforce) / self.tvel) ** 2 * self.vel

        else:
            self.rect.y -= 2
            self.grounded = False
            self.wasgrounded += 1
            if 0 < self.wasgrounded <= self.coyotetime and not self.jumping:
                # assures you can't slide over small pits without jumping (by using high momentum)
                if self.wasgrounded == 1:
                    self.rect.y += 1
                self.buffering = True
            else:
                if self.vertforce - self.gravity < -self.tvel:
                    self.vertforce = -self.tvel
                else:
                    self.vertforce -= self.gravity

                if self.jumping:
                    if self.jumpholding:
                        self.jumptime += 1
                        if self.jumptime >= self.maxjump and self.jumprelease > 0:
                            if self.vertforce > 0:
                                self.vertforce *= (self.jumprelease - 1) / self.jumprelease
                                self.jumprelease -= 1
                    elif not self.grounded:
                        if self.jumptime < self.minjump:
                            self.jumptime += 1
                        if self.minjump <= self.jumptime <= self.maxjump and self.jumprelease > 0:
                            if self.vertforce > 0:
                                self.vertforce *= (self.jumprelease - 1) / self.jumprelease
                                self.jumprelease -= 1
        if self.grounded:
            self.jumping = False
            self.jumpholding = False
            self.jumptime = 0
            self.jumprelease = self.jumpsmoothing
            self.buffertime = self.coyotetime
            self.wasgrounded = 0
        else:
            self.wasgrounded += 1
        # makes movement visually smooth while still stopping the ability to slide over pits
        # if self.buffertime - 1 == self.coyotetime:
        #     self.rect.y -= 1

    # states of motion
    def idle(self):
        if self.momentum < 0:
            if self.grounded:
                if self.momentum > -self.baseaccel:
                    self.momentum = 0
                else:
                    self.momentum += self.acceleration
            else:
                self.momentum += self.airaccel
        if self.momentum > 0:
            if self.momentum < self.baseaccel:
                self.momentum = 0
            else:
                self.momentum -= self.acceleration
        if -1 < self.momentum < 0 or 0 < self.momentum < 1:
            self.momentum = 0
        if self.momentum >= 0:
            floor(self.momentum)
        else:
            ceil(self.momentum)

    def moveleft(self):
        if not hax.active or not hax.noclip:
            if abs(self.momentum - self.acceleration) < self.vel:
                if self.momentum > 0:
                    self.momentum -= self.acceleration + self.turnrate
                else:
                    self.momentum -= self.acceleration
            else:
                self.momentum = -self.vel
        else:
            self.rect.x -= hax.flyspeed
        self.moving = True

    def moveright(self):
        if not hax.active or not hax.noclip:
            if self.momentum + self.acceleration < self.vel:
                if self.momentum < 0:
                    self.momentum += self.acceleration + self.turnrate
                else:
                    self.momentum += self.acceleration
            else:
                self.momentum = self.vel
        else:
            self.rect.x += hax.flyspeed
        self.moving = True

    def moveup(self):
        if not hax.active or not hax.noclip:
            if self.grounded or self.buffering:
                self.vertforce += self.jumpheight
                self.jumping = True
                self.jumpholding = True
        else:
            self.rect.y -= hax.flyspeed

    def movedown(self):
        if not hax.active or not hax.noclip:
            pass
        else:
            self.rect.y += hax.flyspeed

    # run for character motion
    def move(self):
        # acceleration:vel ratio = 1:8
        # gravity:jumpheight:tvel ratio = 1:20:30

        # change motion values correspondingly
        keys = pygame.key.get_pressed()
        self.gravitycalc()
        self.moving = False

        if self.grounded:
            if self.moving:
                self.acceleration = self.baseaccel
            else:
                self.acceleration = self.deaccel
        else:
            self.acceleration = self.airaccel

        if not cutscene:
            # key input

            if keys[pygame.K_p] and hax.active and hax.canfly:
                self.rect.y -= hax.flyspeed
            if keys[pygame.K_o]:
                # jesse what the fuck is this
                for i in range(100):
                    if 25 < i <= 75:
                        x = -1
                    else:
                        x = 1
                    if i > 50:
                        y = -1
                    else:
                        y = 1
                    particlesys.add(pos=plat.rect.center, vel=[10, 10],
                                    mass=8, decay=0, gravity=0, color=(190, 195, 199), delay=i)
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.moveleft()
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.moveright()

            if keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]:
                self.moveup()
            else:
                self.jumpholding = False

            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.movedown()

            if not self.moving:
                self.idle()

        if self.momentum < self.vel * -1:
            self.momentum = self.vel * -1
        if self.momentum > self.vel:
            self.momentum = self.vel

        # collision
        self.rect.x += self.momentum
        collidedtiles = pygame.sprite.spritecollide(self, collidetiles, False)

        for tile1 in collidedtiles:
            if self.momentum > 0:
                self.rect.right = tile1.rect.left
                self.momentum = 0
            elif self.momentum < 0:
                self.rect.left = tile1.rect.right
                self.momentum = 0
        if self.rect.right > width:
            self.rect.right = width
            self.momentum = 0
        if self.rect.left < 0:
            self.rect.left = 0
            self.momentum = 0

        self.rect.y -= self.vertforce
        collidedtiles = pygame.sprite.spritecollide(self, collidetiles, False)

        for tile1 in collidedtiles:
            if self.vertforce < 0:
                self.rect.bottom = tile1.rect.top
                self.vertforce = 0
            elif self.vertforce > 0:
                self.rect.top = tile1.rect.bottom
                self.vertforce = 0
            elif self.transportmomentum < 0:
                self.rect.left = tile1.rect.right
            elif self.transportmomentum > 0:
                self.rect.right = tile1.rect.left
        if self.rect.bottom > height:
            self.rect.bottom = height
            self.vertforce = 0
        if self.rect.top < 0:
            self.rect.top = 0
            self.vertforce = 0

        self.transportmomentum = 0
        collidedtiles = pygame.sprite.spritecollide(self, collidetiles, False)
        if len(collidedtiles) > 0:
            if not hax.active or not hax.noclip:
                if not mute:
                    crush.play()
                self.die("crushed", collidedtiles)

    # call this method to kill the player
    def die(self, cause="unknown", entity=None):
        if entity is None:
            entity = "unknown"
        if not hax.active or not hax.noclip:
            print(f"Death: {cause} by {entity} at {plat.rect.center}")

            if cause == "game":
                shake()
            if cause == "shot":
                shake(10, 15, 15)
                for i in range(4):
                    particlesys.add(pos=plat.rect.center, vel=[random.randint(-5, 5), random.randint(-5, 5)],
                                    mass=random.randint(16, 20),
                                    decay=0.75, gravity=0, color=(190, 195, 199))
                if not mute:
                    shotkill.play()
            if cause == "lava":
                shake(45, 2, 2, 0, 0)
                if not mute:
                    melt.play()
            if cause == "crushed":
                shake()
                for i in range(16):
                    particlesys.add(pos=self.rect.center, vel=[random.randint(-5, 5),
                                                               random.randint(-5, 5)], gravity=0, mass=15,
                                    decay=0.75, color=(190, 195, 199))

            self.alive = False
            tiles.update()
            projectiles.update()
            self.rect.x = spawn.x + size / 4
            self.rect.y = spawn.y + size / 2
            self.alive = True


# particle system
class Particle(object):
    particles = []
    heldparticles = []

    def __init__(self):
        pass

    def add(self, pos=None, vel=None, mass=None, decay=None, gravity=None, color=None, delay=None):
        if pos is None:
            pos = [400, 500]
        pos = list(pos)
        if vel is None:
            vel = [random.randint(0, 20) / 10 - 1, -2]
        if mass is None:
            mass = random.randint(4, 6)
        if decay is None:
            decay = 0.1
        if gravity is None:
            gravity = abs(vel[1] / 20)
        if color is None:
            color = (255, 255, 255)
        if delay is None:
            delay = 0
        if delay == 0:
            self.particles.append({'pos': pos,
                                   'vel': vel,
                                   'mass': mass,
                                   'decay': decay,
                                   'gravity': gravity,
                                   'color': color})
        else:
            self.heldparticles.append({'pos': pos,
                                       'vel': vel,
                                       'mass': mass,
                                       'decay': decay,
                                       'gravity': gravity,
                                       'color': color,
                                       'delay': delay})

    def run(self, shape="circle"):
        for particle in self.particles:
            particle['pos'][0] += particle['vel'][0]
            particle['pos'][1] += particle['vel'][1]
            particle['mass'] -= particle['decay']
            particle['vel'][1] += particle['gravity']

            if shape == "circle":
                pygame.draw.circle(win, particle['color'], [particle['pos'][0], particle['pos'][1]],
                                   particle['mass'])
            if shape == "square":
                pygame.draw.rect(win, particle['color'], [particle['pos'][0] - particle['mass'] / 2,
                                                          particle['pos'][1] - particle['mass'] / 2,
                                                          particle['mass'], particle['mass']])

            if particle['mass'] <= 0 or \
                    not 0 < particle['pos'][0] <= width - particle['mass'] / 2 or \
                    not particle['pos'][0] <= height - particle['mass'] / 2:
                self.particles.remove(particle)

        for particle in self.heldparticles:
            if particle['delay'] <= 0:
                del particle['delay']
                self.particles.append(dict(particle))
        self.heldparticles[:] = [particle for particle in self.heldparticles if 'delay' in particle and
                                 particle['delay'] > 0]
        for particle in self.heldparticles:
            particle['delay'] -= 1


# noinspection PyArgumentList
@unique
class Direction(Enum):
    up = auto()
    left = auto()
    down = auto()
    right = auto()


# dummy class for power()
class Demo(pygame.sprite.Sprite):
    def __init__(self, image, rect):
        super().__init__()
        self.image = image
        self.rect = rect


# surrounding check for a tile's connection to power
def power(image, rect):
    powered.clear()

    tempsprite = Demo(image, rect)

    tempsprite.rect.y -= 1
    uppower = pygame.sprite.spritecollide(tempsprite, rocktiles, False)
    upblock = pygame.sprite.spritecollide(tempsprite, doortiles, False)
    tempsprite.rect.y += 1

    tempsprite.rect.x -= 1
    leftpower = pygame.sprite.spritecollide(tempsprite, rocktiles, False)
    leftblock = pygame.sprite.spritecollide(tempsprite, doortiles, False)
    tempsprite.rect.x += 1

    tempsprite.rect.y += 1
    downpower = pygame.sprite.spritecollide(tempsprite, rocktiles, False)
    downblock = pygame.sprite.spritecollide(tempsprite, doortiles, False)
    tempsprite.rect.y -= 1

    tempsprite.rect.x += 1
    rightpower = pygame.sprite.spritecollide(tempsprite, rocktiles, False)
    rightblock = pygame.sprite.spritecollide(tempsprite, doortiles, False)
    tempsprite.rect.x -= 1

    ispowered = False

    if len(uppower) > len(upblock):
        powered.append(Direction.up)
        ispowered = True
    if len(leftpower) > len(leftblock):
        powered.append(Direction.left)
        ispowered = True
    if len(downpower) > len(downblock):
        powered.append(Direction.down)
        ispowered = True
    if len(rightpower) > len(rightblock):
        powered.append(Direction.right)
        ispowered = True

    return ispowered


# image glitching
def glitch(image):
    global glitchimg
    random.seed(random.randint(1, 20000000))
    x = random.random()
    glitchimg = glitcher.glitch_image(src_img=image, glitch_amount=5, seed=x, color_offset=True, frames=1)
    glitchimg.save(r"assets\img\anims\glitchimg.png", format="PNG")


# anim system
def animate():
    global cutscene
    global cutscenecount
    global animtime
    global tempsurf
    global zoom
    global animlive
    global screenshake
    global screenrotation
    global mute
    global animsound

    if animlive:
        if cutscenecount == 0:

            if animtime == 0:
                plat.jumpheight = 1
                plat.gravity = 1
                plat.vel = 1
                mute = True
                animsound = pygame.mixer.Sound("assets/sfx/anims/anim1glitch.ogg")
            if 20 < animtime < 50:
                plat.moveleft()
            if animtime == 55:
                vortextiles.update()
                shake(30, 5, 5, 1, 1)
                animsound.play()
                animsound = pygame.mixer.Sound("assets/sfx/anims/anim1glitch2.ogg")
            if 55 <= animtime < 60:
                plat.acceleration = 2
                plat.vel = 4
                plat.moveup()
                plat.moveright()
            if 60 <= animtime < 90:
                plat.idle()
            if 90 <= animtime < 240:
                vortextiles.update()
                if animtime % 2 != 0:
                    plat.rect.x -= int((animtime - 90) / 10)
            if animtime == 110:
                animsound.play()
                animsound.play()
                animsound.play()
                animsound = pygame.mixer.Sound("assets/sfx/anims/anim1glitch3.ogg")
            if 110 <= animtime < 260:
                screenrotation = (animtime - 109) * (90 / 150)
            if 180 <= animtime < 260:
                zoom += 4.5 / 80
            if 110 <= animtime < 180:
                plat.moveup()
                plat.moveright()
                tempsurf = pygame.Surface((width * 3, height * 3), pygame.SRCALPHA)
                pygame.draw.rect(tempsurf, (colors.DPURPLE[0], colors.DPURPLE[1], colors.DPURPLE[2],
                                            (2 * animtime - 180)), tempsurf.get_rect())
                shake(1, int((animtime - 100) / 10), int((animtime - 100) / 10), 0, 0)
                screenrotation = (animtime - 109) * (90 / 130)
            if 180 <= animtime < 300:
                pygame.draw.rect(tempsurf,
                                 (colors.DPURPLE[0], colors.DPURPLE[1], colors.DPURPLE[2], 2 * 180 - 180),
                                 tempsurf.get_rect())
                shake(1, int((animtime - 100) / 10), int((animtime - 100) / 10), 0, 0)
            if animtime == 300:
                animsound.play()
                animsound = pygame.mixer.Sound("assets/sfx/anims/anim1glitch4.ogg")
            if animtime == 360:
                vortextiles.update("assets/img/escape.png")
                vortextiles.update("assets/img/spawn.png", 1)
                shake(10, 5, 5, 0, 0)
                tempsurf = pygame.Surface((screenwidth, screenheight), pygame.SRCALPHA)
                animsound.play()
            if 420 <= animtime < 570:
                zoom -= 15.5 / 150
            if 420 <= animtime < 480:
                screenrotation -= 1.5
            if animtime == 510:
                mute = False
            if animtime == 920:
                animlive = False

        animtime += 1

    else:
        cutscene = False
        cutscenecount += 1
        plat.baseaccel = 1
        plat.airaccel = 0.5
        plat.acceleration = 0
        plat.vel = 8
        plat.vertforce = 0
        plat.gravity = 0.7
        plat.jumpheight = 14
        plat.tvel = 21
        plat.jumping = False
        plat.grounded = False
        plat.escaped = True
        zoom = 1
        screenshake = [0, 0]
        screenrotation = 0
        mute = False


# screenshake
def shake(shakeduration=30, xshakeintensity=20, yshakeintensity=20, xshakedecay=1, yshakedecay=1):
    global screenshake, shaketime, shakeintensity, shakedecay

    shaketime = shakeduration
    shakeintensity = [xshakeintensity, yshakeintensity]
    shakedecay = [xshakedecay, yshakedecay]


# push things around
def push(direction, *instigators):
    nextcollide = []
    for entity in instigators:
        tempgroup = pygame.sprite.Group([s for s in solidtiles if s != entity])
        collided = pygame.sprite.spritecollide(entity, tempgroup, False)
        for collision in collided:
            nextcollide.append(collision)
        if collided:
            if direction == Direction.up:
                for collision in collided:
                    collision.rect.bottom = entity.rect.top
            if direction == Direction.left:
                for collision in collided:
                    collision.rect.right = entity.rect.left
            if direction == Direction.down:
                for collision in collided:
                    collision.rect.top = entity.rect.bottom
            if direction == Direction.left:
                for collision in collided:
                    collision.rect.left = entity.rect.right
    if nextcollide:
        push(direction, *nextcollide)


# tile parent classes
class Tile(pygame.sprite.Sprite):
    def __init__(self, img, x=0, y=0, convert_alpha=False, rotate=0):
        super().__init__()
        self.x = x
        self.y = y
        if convert_alpha:
            self.image = pygame.image.load(img).convert_alpha()
        else:
            self.image = pygame.image.load(img)
        self.image = pygame.transform.rotate(self.image, rotate * 90)

        if rotate == 0:
            self.direction = Direction.up
        if rotate == 1:
            self.direction = Direction.left
        if rotate == 2:
            self.direction = Direction.down
        if rotate == 3:
            self.direction = Direction.right
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

    def update(self):
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y


class TempObj(pygame.sprite.Sprite):
    def __init__(self, img, x=0, y=0, convert_alpha=False):
        super().__init__()
        if convert_alpha:
            self.image = pygame.image.load(img).convert_alpha()
            self.mask = pygame.mask.from_surface(self.image)
        else:
            self.image = pygame.image.load(img)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

    def update(self):
        if not plat.alive:
            self.kill()


# tile types
class Space(Tile):
    def __init__(self, x, y):
        super().__init__("assets/img/space.png", x, y)


class Block(Tile):
    def __init__(self, x, y):
        super().__init__("assets/img/block.png", x, y)


class Spawn(Tile):
    def __init__(self, x, y):
        super().__init__("assets/img/spawn.png", x, y)
        if invisiblespawn:
            self.image = pygame.image.load("assets/img/space.png")
            self.rect = self.image.get_rect()


class Lava(Tile):
    def __init__(self, x, y):
        super().__init__("assets/img/lava.png", x, y)


class Esc(Tile):
    def __init__(self, x, y):
        super().__init__("assets/img/escape.png", x, y)


class Elev(Tile):
    def __init__(self, x, y, speed=2):
        super().__init__("assets/img/elevator.png", x, y)
        self.direction = 0
        self.speed = speed
        self.lastcollide = 1

    def update(self):
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y
            self.direction = Direction.up

        else:
            if power(self.image, self.rect):
                pass
            else:
                if hax.active and hax.bumpyride:
                    charcollide = pygame.sprite.collide_rect(self, plat)
                else:
                    plat.rect.y += self.speed + 1
                    charcollide = pygame.sprite.collide_rect(self, plat)
                    plat.rect.y -= self.speed + 1

                self.rect.y -= self.speed
                upcollidedtiles = pygame.sprite.spritecollide(self, circuittiles, False)
                upcanmove = pygame.sprite.spritecollide(self, elevcollidetiles, False)
                self.rect.y += self.speed

                self.rect.x -= self.speed
                leftcollidedtiles = pygame.sprite.spritecollide(self, circuittiles, False)
                leftcanmove = pygame.sprite.spritecollide(self, elevcollidetiles, False)
                self.rect.x += self.speed

                self.rect.y += self.speed
                downcollidedtiles = pygame.sprite.spritecollide(self, circuittiles, False)
                downcanmove = pygame.sprite.spritecollide(self, elevcollidetiles, False)
                self.rect.y -= self.speed

                self.rect.x += self.speed
                rightcollidedtiles = pygame.sprite.spritecollide(self, circuittiles, False)
                rightcanmove = pygame.sprite.spritecollide(self, elevcollidetiles, False)
                self.rect.x -= self.speed

                # jumping right next to an elevator makes you fly (feature?)
                # but only when you jump on the left side while the elevator moves left
                # keeping bc funy

                if self.direction == Direction.up:
                    if (len(upcanmove) == 0 or upcanmove[0].rect.bottom != self.rect.top) and \
                            len(upcollidedtiles) > 0:
                        if len(upcanmove) == 0:
                            self.rect.y -= self.speed
                        else:
                            self.rect.top = upcanmove[0].rect.bottom
                            self.direction = Direction.left

                        if charcollide or pygame.sprite.collide_rect(self, plat):
                            if len(upcanmove) == 0:
                                plat.rect.y -= self.speed
                            else:
                                plat.rect.y -= abs(self.rect.top - upcanmove[0].rect.bottom)
                    else:
                        self.direction = Direction.left

                if self.direction == Direction.left:
                    if (len(leftcanmove) == 0 or leftcanmove[0].rect.right != self.rect.left) and \
                            len(leftcollidedtiles) > 0:
                        if len(leftcanmove) == 0:
                            self.rect.x -= self.speed
                        else:
                            self.rect.left = leftcanmove[0].rect.right
                            self.direction = Direction.down

                        if charcollide or pygame.sprite.collide_rect(self, plat):
                            plat.transportmomentum = -self.speed
                            if len(leftcanmove) == 0:
                                plat.rect.x -= self.speed
                            else:
                                plat.rect.x -= abs(self.rect.left - leftcanmove[0].rect.right)
                    else:
                        self.direction = Direction.down

                if self.direction == Direction.down:
                    if (len(downcanmove) == 0 or downcanmove[0].rect.top != self.rect.bottom) \
                            and len(downcollidedtiles) > 0:
                        if len(downcanmove) == 0:
                            self.rect.y += self.speed
                        else:
                            self.rect.bottom = downcanmove[0].rect.top
                            self.direction = Direction.right

                        # lastcollide stops the player from seemingly hopping after running off an elevator
                        # the reason behind hopping is that the elevator moves down, but the player doesn't get
                        # pulled down because he has ceased contact with the elevator
                        if charcollide or pygame.sprite.collide_rect(self, plat):
                            self.lastcollide = -1
                            collision = True
                            if plat.grounded:
                                if plat.rect.left < self.rect.left:
                                    self.rect.x -= 2
                                    collidedtiles = pygame.sprite.spritecollide(self, collidetiles, False)
                                    self.rect.x += 2
                                    if len(collidedtiles) == 3:
                                        collision = False
                                if plat.rect.right < self.rect.right:
                                    self.rect.x += 2
                                    collidedtiles = pygame.sprite.spritecollide(self, collidetiles, False)
                                    self.rect.x -= 2
                                    if len(collidedtiles) == 3:
                                        collision = False
                            if collision:
                                if len(downcanmove) == 0:
                                    plat.rect.y += self.speed
                                else:
                                    plat.rect.y += abs(self.rect.top - downcanmove[0].rect.top)
                    else:
                        self.direction = Direction.right

                if self.direction == Direction.right:
                    if (len(rightcanmove) == 0 or rightcanmove[0].rect.left != self.rect.right) \
                            and len(rightcollidedtiles) > 0:
                        if len(rightcanmove) == 0:
                            self.rect.x += self.speed
                        else:
                            self.rect.right = upcanmove[0].rect.left
                            self.direction = Direction.up

                        if charcollide or pygame.sprite.collide_rect(self, plat):
                            plat.transportmomentum = self.speed
                            if len(rightcanmove) == 0:
                                plat.rect.x += self.speed
                            else:
                                plat.rect.x += abs(self.rect.right - rightcanmove[0].rect.left)
                    else:
                        self.direction = Direction.up

            if self.lastcollide == -1:
                plat.vertforce -= self.speed
                self.lastcollide += 1


class Circuit(Tile):
    def __init__(self, x, y):
        super().__init__("assets/img/circuit.png", x, y)


class Switch(Tile):
    def __init__(self, x, y, ident):
        super().__init__("assets/img/switch.png", x, y, True)
        self.ident = ident
        self.pressed = False

    def update(self):
        if pygame.sprite.collide_mask(self, plat):
            if not self.pressed:
                self.pressed = True
                press.play()
                self.image = pygame.image.load("assets/img/switch2.png").convert_alpha()
                self.mask = pygame.mask.from_surface(self.image)
                doortiles.update(self.ident)
                print(f"Signal: ID {self.ident}")

        else:
            if pygame.sprite.collide_rect(self, plat):
                pass
            else:
                self.pressed = False
                self.image = pygame.image.load("assets/img/switch.png").convert_alpha()
                self.mask = pygame.mask.from_surface(self.image)


class Door(Tile):
    def __init__(self, x, y, ident):
        super().__init__("assets/img/door.png", x, y, True)
        self.ident = ident

    def update(self, ident=-1):
        if not plat.alive:
            self.add(sprites2, collidetiles, elevcollidetiles, bulletcollidetiles)

        else:
            if self.ident == ident:
                if sprites2.has(self):
                    self.kill()
                    self.add(doortiles, tiles)
                else:
                    self.add(sprites2, collidetiles, elevcollidetiles, bulletcollidetiles)


class Rock(Tile):
    def __init__(self, x, y):
        super().__init__("assets/img/hotrock.png", x, y)


class Turret(Tile):
    def __init__(self, x, y, firerate=60, delay=0):
        super().__init__("assets/img/turret.png", x, y)
        self.firerate = firerate
        self.delay = delay
        self.delaystorage = delay
        self.cooldown = 0

    def update(self):
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y

            self.delay = self.delaystorage
            self.cooldown = 0

        else:
            if self.delay > 0:
                self.delay -= 1
            else:
                if self.cooldown > 0:
                    self.cooldown -= 1

                if self.cooldown <= 0:

                    power(self.image, self.rect)

                    if Direction.up in powered:
                        projectiles.add(Bullet(self.rect.midbottom[0] - size / 8, self.rect.midbottom[1] + size / 4,
                                               Direction.down))
                    if Direction.left in powered:
                        projectiles.add(Bullet(self.rect.midright[0] + size / 4, self.rect.midright[1] - size / 8,
                                               Direction.right))
                    if Direction.down in powered:
                        projectiles.add(Bullet(self.rect.midtop[0] - size / 8, self.rect.midtop[1] - size / 4,
                                               Direction.up))
                    if Direction.right in powered:
                        projectiles.add(Bullet(self.rect.midleft[0] - size / 4, self.rect.midleft[1] - size / 8,
                                               Direction.left))
                    self.cooldown = self.firerate
                    if not mute:
                        shoot.play()


class Bullet(TempObj):
    def __init__(self, x, y, direction, speed=5):
        super().__init__("assets/img/bullet.png", x, y)
        self.rect.x, self.rect.y = x, y
        self.direction = direction
        self.speed = speed

    def update(self):
        if not plat.alive:
            self.kill()

        if self.direction == Direction.up:
            self.rect.y -= self.speed
        if self.direction == Direction.left:
            self.rect.x -= self.speed
        if self.direction == Direction.down:
            self.rect.y += self.speed
        if self.direction == Direction.right:
            self.rect.x += self.speed

        collide = pygame.sprite.spritecollide(self, bulletcollidetiles, False)
        charcollide = pygame.sprite.collide_rect(self, plat)
        if collide or self.rect.left < 0 or self.rect.right > width or self.rect.top < 0 or self.rect.bottom > height:
            self.kill()
            if not mute:
                hit.play()
        if charcollide:
            self.kill()
            plat.die("shot", self)


class Light(Tile):
    def __init__(self, x, y):
        super().__init__("assets/img/stealth/light.png", x, y)

    def update(self):
        lightingtiles.empty()
        power(self.image, self.rect)

        if Direction.up in powered:
            lightingtiles.add(Lighting(self.rect.midbottom[0] - width / 2, self.rect.midbottom[1], 0))
        if Direction.left in powered:
            lightingtiles.add(Lighting(self.rect.midright[0], self.rect.midright[1] - width / 2, 90))
        if Direction.down in powered:
            lightingtiles.add(Lighting(self.rect.midtop[0] - width / 2, self.rect.midtop[1], 180))
        if Direction.right in powered:
            lightingtiles.add(Lighting(self.rect.midleft[0], self.rect.midleft[1] - width / 2, 270))


class Lighting(Tile):
    def __init__(self, x, y, rotation=0, angle=75.0, offset=16, inverse=False, filler=False):
        super().__init__("assets/img/stealth/lighting.png", x, y)
        self.rotation = rotation
        self.angle = angle
        self.offset = offset
        self.length = 1
        self.inverse = inverse
        self.filler = filler
        self.funclength = self.length + self.offset
        self.vec1 = pygame.math.Vector2()
        self.vec2 = pygame.math.Vector2()
        self.set = False

    def update(self):
        if not self.set:
            self.set = True
            self.rect.x, self.rect.y = self.x, self.y

            if not self.inverse:
                lightingtiles.add(Lighting(self.rect.x, self.rect.y, self.rotation, self.angle, -self.offset,
                                           filler=False))
            if self.offset > 0:
                lightingtiles.add(Lighting(self.rect.x, self.rect.y, self.rotation, self.angle, self.offset - 1,
                                           filler=True))
            if self.offset < 0:
                lightingtiles.add(Lighting(self.rect.x, self.rect.y, self.rotation, self.angle, self.offset + 1,
                                           filler=True))
            if self.angle > 0:
                lightingtiles.add(Lighting(self.rect.x, self.rect.y, self.rotation, self.angle - 5, self.offset,
                                           filler=False))

        if not self.inverse:
            if self.rotation == 0:
                self.vec1 = pygame.math.Vector2()


class Vortex(Tile):
    def __init__(self, x, y, ident, image, startimage):
        super().__init__(startimage, x, y)
        self.ident = ident
        self.rawimg = image

    def update(self, image="", ident=0):
        if ident == self.ident:
            glitch(self.rawimg)
            self.rawimg = glitchimg
            if image == "":
                self.image = pygame.image.load("assets/img/anims/glitchimg.png")
            else:
                self.image = pygame.image.load(image)


class Piston(Tile):
    def __init__(self, x, y, ident, rotation=0):
        super().__init__("assets/img/piston.png", x, y, convert_alpha=True, rotate=rotation)
        self.ident = ident
        self.rotation = rotation
        self.set = False

    def update(self):
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y

        if not self.set:
            entity = PistonRod(self.rect.x, self.rect.y, self.ident, self, self.rotation)
            entity.add(pistonrodtiles, sprites, elevcollidetiles, bulletcollidetiles, solidtiles, collidetiles, tiles)
            self.set = True

        if self.rect.x != self.x or self.rect.y != self.y:
            if power(self.image, self.rect):
                pistonrodtiles.update(self.ident, True, self.rect.x, self.rect.y)
            else:
                pistonrodtiles.update(self.ident, self.rect.x, self.rect.y)
        else:
            if power(self.image, self.rect):
                pistonrodtiles.update(self.ident, True)
            else:
                pistonrodtiles.update(self.ident)
        # print(self.rect)


class PistonRod(Tile):
    def __init__(self, x, y, ident, host, rotation=0, speed=2):
        super().__init__("assets/img/pistonrod.png", x, y, convert_alpha=True, rotate=rotation)
        self.ident = ident
        self.host = host
        self.rotation = rotation
        self.distance = 0
        self.speed = speed
        self.active = False

    def update(self, ident=-1, active=False):
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y

        if self.host.rect.x - self.rect.x != 0 or self.host.rect.y - self.rect.y != 0:
            self.rect = self.host.rect

        if active:
            if self.rect == self.host.rect:
                self.active = True
        else:
            self.active = False

        if self.ident == ident:
            if self.rotation % 2 == 0:
                if self.host.rect.x - self.rect.x != 0 or abs(self.host.rect.y - self.rect.y) != self.distance:
                    self.rect.x = self.host.rect.x
                    self.rect.y += self.host.rect.y - self.rect.y
            else:
                if self.host.rect.y - self.rect.y != 0 or abs(self.host.rect.x - self.rect.x) != self.distance:
                    self.rect.y = self.host.rect.y
                    self.rect.x += self.host.rect.x - self.rect.x
            # one collision for self, one collision for host piston, one collision for the obstructive tile
            if len(pygame.sprite.spritecollide(self, solidtiles, False)) >= 3:
                self.kill()

            if self.active:
                if self.direction == Direction.up:
                    if abs(self.host.rect.y - self.rect.y) + self.speed <= 32:
                        self.distance += self.speed
                    else:
                        self.distance = self.host.rect.y - 32
                    self.rect.y = self.host.rect.y - self.distance
                if self.direction == Direction.left:
                    if abs(self.host.rect.x - self.rect.x) + self.speed <= 32:
                        self.rect.x -= self.speed
                    else:
                        self.rect.x = self.host.rect.x - 32
                if self.direction == Direction.down:
                    if abs(self.host.rect.y - self.rect.y) + self.speed <= 32:
                        self.rect.y += self.speed
                    else:
                        self.rect.y = self.host.rect.y + 32
                if self.direction == Direction.right:
                    if abs(self.host.rect.x - self.rect.x) + self.speed <= 32:
                        self.rect.x += self.speed
                    else:
                        self.rect.x = self.host.rect.x + 32

                if pygame.sprite.spritecollide(self, solidtiles, False):
                    push(self.direction, self)
            else:
                if self.direction == Direction.up:
                    if abs(self.host.rect.y - self.rect.y) - self.speed >= 0:
                        self.rect.y += self.speed
                    else:
                        self.rect.y = self.host.rect.y
                if self.direction == Direction.left:
                    if abs(self.host.rect.x - self.rect.x) - self.speed >= 0:
                        self.rect.x += self.speed
                    else:
                        self.rect.x = self.host.rect.x
                if self.direction == Direction.down:
                    if abs(self.host.rect.y - self.rect.y) - self.speed >= 0:
                        self.rect.y -= self.speed
                    else:
                        self.rect.y = self.host.rect.y
                if self.direction == Direction.right:
                    if abs(self.host.rect.x - self.rect.x) - self.speed >= 0:
                        self.rect.x -= self.speed
                    else:
                        self.host.rect.x = self.rect.x


# refresh every frame
def redrawgamewindow():
    for sprite in spritesbg:
        win.blit(sprite.image, (sprite.rect.x + screenshake[0], sprite.rect.y + screenshake[1]))
    for sprite in sprites:
        win.blit(sprite.image, (sprite.rect.x + screenshake[0], sprite.rect.y + screenshake[1]))
    for sprite in sprites2:
        win.blit(sprite.image, (sprite.rect.x + screenshake[0], sprite.rect.y + screenshake[1]))
    for sprite in projectiles:
        win.blit(sprite.image, (sprite.rect.x + screenshake[0], sprite.rect.y + screenshake[1]))
    if particlesys.particles or particlesys.heldparticles:
        particlesys.run("square")
    win.blit(leveltext, (4, 1024))
    win.blit(plat.image, (plat.rect.x + screenshake[0], plat.rect.y + screenshake[1]))
    for sprite in vortextiles:
        win.blit(sprite.image, (sprite.rect.x + screenshake[0], sprite.rect.y + screenshake[1]))
    if len(lighttiles) > 0:
        win.blit(lights, (screenshake[0], screenshake[1]), special_flags=pygame.BLEND_RGBA_SUB)
    win.blit(tempsurf, (0, 0))
    pygame.display.flip()


# final inits
plat = Player()
plat.rect.x, plat.rect.y = 100, 100
particlesys = Particle()

font1 = fonts.Font("assets/data/fonts/pixel-piss.ttf", 20)
leveltext = font1.render("???", False, colors.WHITE)

# main loop
run = True
while run:
    start_time = timeit.default_timer()
    clock.tick(framerate)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.mod & pygame.KMOD_CTRL:
                if pygame.key.get_pressed()[pygame.K_w]:
                    run = False

    if plat.escaped is True:
        plat.escaped = False
        levelcount += 1
        if not cutscene:
            currentlvl = levels[levelcount]
            leveltext = font1.render(f"Level {levelcount + 1} : {leveldescs[levelcount]}", False, colors.WHITE)
        else:
            currentlvl = anims[cutscenecount]
            leveltext = font1.render("", False, colors.WHITE)

        # clears old tile data
        spacetiles.empty()
        blocktiles.empty()
        spawn = None
        lavatiles.empty()
        esctiles.empty()
        elevtiles.empty()
        circuittiles.empty()
        switchtiles.empty()
        doortiles.empty()
        rocktiles.empty()
        turrettiles.empty()
        bullets.empty()
        pistontiles.empty()
        pistonrodtiles.empty()

        stealth = False
        lighttiles.empty()
        lightingtiles.empty()

        spritesbg.empty()
        sprites.empty()
        sprites2.empty()
        projectiles.empty()
        collidetiles.empty()
        elevcollidetiles.empty()
        bulletcollidetiles.empty()
        solidtiles.empty()
        tiles.empty()

        # loads level data
        for strip in currentlvl:
            for tile in strip:
                bgloaded = False
                if tile == 0:
                    spacetiles.add(Space(levelx, levely))
                    bgloaded = True
                if tile == 1:
                    blocktiles.add(Block(levelx, levely))
                if tile == 2:
                    spawn = Spawn(levelx, levely)
                if tile == 3:
                    lavatiles.add(Lava(levelx, levely))
                    bgloaded = True
                if tile == 4:
                    esctiles.add(Esc(levelx, levely))
                if tile == 5:
                    circuittiles.add(Circuit(levelx, levely))
                    bgloaded = True
                    elevtiles.add(Elev(levelx, levely))
                if tile == 6:
                    circuittiles.add(Circuit(levelx, levely))
                    bgloaded = True
                if tile == 9:
                    rocktiles.add(Rock(levelx, levely))
                if tile == 11:
                    lighttiles.add(Light(levelx, levely))
                if type(tile) == list:
                    if tile[0] == 5:
                        circuittiles.add(Circuit(levelx, levely))
                        bgloaded = True
                        elevtiles.add(Elev(levelx, levely, tile[1]))
                    if tile[0] == 7:
                        spacetiles.add(Space(levelx, levely))
                        bgloaded = True
                        switchtiles.add(Switch(levelx, levely, tile[1]))
                    if tile[0] == 8:
                        if tile[2] == 0:
                            spacetiles.add(Space(levelx, levely))
                            bgloaded = True
                        if tile[2] == 1:
                            blocktiles.add(Block(levelx, levely))
                        if tile[2] == 3:
                            lavatiles.add(Lava(levelx, levely))
                            bgloaded = True
                        if tile[2] == 4:
                            esctiles.add(Esc(levelx, levely))
                        if tile[2] == 5:
                            circuittiles.add(Circuit(levelx, levely))
                            bgloaded = True
                            elevtiles.add(Elev(levelx, levely))
                        if tile[2] == 6:
                            circuittiles.add(Circuit(levelx, levely))
                            bgloaded = True
                        if tile[2] == 9:
                            rocktiles.add(Rock(levelx, levely))
                        if tile[2] == 10:
                            if len(tile) == 5:
                                turrettiles.add(Turret(levelx, levely, tile[3], tile[4]))
                            elif len(tile) == 4:
                                turrettiles.add(Turret(levelx, levely, tile[3]))
                            else:
                                turrettiles.add(Turret(levelx, levely))
                        if tile[2] == 11:
                            lighttiles.add(Light(levelx, levely))

                        doortiles.add(Door(levelx, levely, tile[1]))
                    if tile[0] == 10:
                        if len(tile) == 3:
                            turrettiles.add(Turret(levelx, levely, tile[1], tile[2]))
                        elif len(tile) == 2:
                            turrettiles.add(Turret(levelx, levely, tile[1]))
                        else:
                            turrettiles.add(Turret(levelx, levely))
                    if tile[0] == 12:
                        vortextiles.add(Vortex(levelx, levely, tile[1], "assets/img/anims/greenglitch.png",
                                               "assets/img/escape.png"))
                        # if tile[1] == 0:
                        #     prevortextiles.append([levelx, levely, "assets/img/space.png"])
                        # if tile[1] == 1:
                        #     prevortextiles.append([levelx, levely, "assets/img/block.png"])
                        # if tile[1] == 2:
                        #     prevortextiles.append([levelx, levely, "assets/img/spawn.png"])
                        # if tile[1] == 3:
                        #     prevortextiles.append([levelx, levely, "assets/img/lava.png"])
                        # if tile[1] == 4:
                        #     prevortextiles.append([levelx, levely, "assets/img/escape.png"])
                        # if tile[1] == 5:
                        #     prevortextiles.append([levelx, levely, "assets/img/circuit.png"])
                        # if tile[1] == 6:
                        #     prevortextiles.append([levelx, levely, "assets/img/elevator.png"])
                    if tile[0] == 13:
                        pistontiles.add(Piston(levelx, levely, tile[1]))

                if not bgloaded:
                    spacetiles.add(Space(levelx, levely))

                levelx += 1 * size
            levelx = 0
            levely += 1 * size
        levely = 0

        if spawn is None:
            print("Error: No spawn found")
            run = False
        if len(lighttiles) > 0:
            stealth = True

        spritesbg.add(spacetiles, lavatiles, circuittiles)
        sprites.add(blocktiles, spawn, esctiles, rocktiles, turrettiles, lighttiles, pistonrodtiles)
        sprites2.add(elevtiles, switchtiles, doortiles, pistontiles)
        projectiles.add(bullets)
        elevcollidetiles.add(spacetiles, blocktiles, spawn, lavatiles, esctiles, switchtiles, doortiles, rocktiles,
                             turrettiles, lighttiles, pistontiles, pistonrodtiles)
        bulletcollidetiles.add(blocktiles, elevtiles, doortiles, rocktiles, turrettiles, lighttiles, pistontiles,
                               pistonrodtiles)
        solidtiles.add(bulletcollidetiles, bullets)
        collidetiles.add(solidtiles)
        tiles.add(spritesbg, sprites, sprites2)

        plat.die("respawn", "game")

    if pygame.sprite.spritecollide(plat, lavatiles, False):
        plat.die("lava", pygame.sprite.spritecollide(plat, lavatiles, False))
    if pygame.sprite.spritecollide(plat, esctiles, False):
        cutscene = False
        invisiblespawn = False
        if levelcount == 4 - 1:
            cutscene = True
            invisiblespawn = True
            zoom = 12
            plat.momentum = 0
            plat.vertforce = 0
            animlive = True
        plat.escaped = True
    if cutscene:
        animate()

    if shaketime > 0 and shakeintensity[0] > 0 and shakeintensity[1] > 0:
        screenshake[0] = random.randrange(-shakeintensity[0], shakeintensity[0])
        screenshake[1] = random.randrange(-shakeintensity[1], shakeintensity[1])

        shaketime -= 1
        shakeintensity[0] -= shakedecay[0]
        shakeintensity[1] -= shakedecay[1]
    else:
        shaketime = 0
        shakeintensity = [0, 0]
        screenshake = [0, 0]

    elevtiles.update()
    switchtiles.update()
    turrettiles.update()
    pistontiles.update()
    projectiles.update()
    lighttiles.update()
    plat.move()

    if stealth:
        lights.fill(colors.DGRAY)
        lightingtiles.update()

    # reset game window
    win = pygame.Surface((screenwidth / zoom, screenheight / zoom))
    win.fill((0, 0, 0))
    redrawgamewindow()
    screen.blit(pygame.transform.scale(pygame.transform.rotate(win, screenrotation),
                                       screen.get_size()), (0, 0))

    # print(timeit.default_timer() - start_time)
pygame.quit()
