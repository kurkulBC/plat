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
import timeit
from assets.data import shadowcasting

# init ~1.7s
pygame.init()
hax.active = False
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
shadowsurf = pygame.Surface((screenwidth, screenheight), pygame.SRCALPHA)

pygame.display.set_caption("Platman")
pygame.display.set_icon(pygame.image.load("assets/img/platterman.png"))
clock = pygame.time.Clock()
levelx = 0
levely = 0
cutscene = False
invisiblespawn = False
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
lights = pygame.surface.Surface((1024, 1024))
stealth = False


# define player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.momentum = 0
        self.baseaccel = 1.5
        self.airaccel = 0.3
        self.deaccel = 4
        self.airdeaccel = 0.5
        self.acceleration = 0
        self.vel = 10
        self.turnrate = 4
        self.transportmomentum = 0
        self.moving = False
        self.alive = True
        self.vertforce = 0
        self.gravity = 1.25
        self.jumpheight = 18
        self.tvel = 30
        self.jumping = False
        self.minjump = 2
        self.maxjump = self.jumpheight / self.gravity
        self.jumpholding = False
        self.jumptime = 0
        self.jumpsmoothing = 5
        self.jumprelease = 0
        self.weight = 0
        self.grounded = True
        self.escaped = True
        self.image = pygame.image.load("assets/img/platterman.png")
        self.rect = self.image.get_rect()
        self.levelcount = -1
        self.coyotetime = 6
        self.buffering = False
        self.wasgrounded = 0
        self.mask = pygame.mask.from_surface(self.image)

    # calculates gravity
    def gravitycalc(self):
        self.buffering = False
        self.rect.y += 2
        grounded = pygame.sprite.spritecollide(self, collidetiles, False)
        self.rect.y -= 2

        if grounded or self.rect.bottom >= height:
            if not self.grounded:
                self.grounded = True
                self.momentum /= 4
                # this line doesn't work because vertforce is always 0 at this point
                # self.momentum /= (abs(self.vertforce + 1) / self.tvel) ** 2 * self.vel

        else:
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
                                self.vertforce /= 3
                                self.jumprelease -= 1
        if self.grounded:
            self.jumping = False
            self.jumpholding = False
            self.jumptime = 0
            self.jumprelease = self.jumpsmoothing
            self.wasgrounded = 0
        else:
            self.wasgrounded += 1

    def changeaccel(self):
        if self.moving:
            if self.grounded:
                self.acceleration = self.baseaccel
            else:
                self.acceleration = self.airaccel
        else:
            if self.grounded:
                self.acceleration = self.deaccel
            else:
                self.acceleration = self.airdeaccel

    # states of motion
    def idle(self):
        if self.momentum < 0:
            if self.grounded:
                if self.momentum > -self.deaccel:
                    self.momentum = 0
                else:
                    self.momentum += self.acceleration
            else:
                if self.momentum > -self.airdeaccel:
                    self.momentum = 0
                else:
                    self.momentum += self.acceleration
        if self.momentum > 0:
            if self.grounded:
                if self.momentum < self.deaccel:
                    self.momentum = 0
                else:
                    self.momentum -= self.acceleration
            else:
                if self.momentum < self.airdeaccel:
                    self.momentum = 0
                else:
                    self.momentum -= self.acceleration

    def moveleft(self):
        self.moving = True
        if not hax.active or not hax.noclip:
            if abs(self.momentum - self.acceleration) < self.vel:
                if self.momentum - self.acceleration * self.turnrate > 0:
                    self.momentum -= self.acceleration * self.turnrate
                else:
                    self.momentum -= self.acceleration
            else:
                self.momentum = -self.vel
        else:
            self.rect.x -= hax.flyspeed

    def moveright(self):
        self.moving = True
        if not hax.active or not hax.noclip:
            if self.momentum + self.acceleration < self.vel:
                if self.momentum + self.acceleration * self.turnrate < 0:
                    self.momentum += self.acceleration * self.turnrate
                else:
                    self.momentum += self.acceleration
            else:
                self.momentum = self.vel
        else:
            self.rect.x += hax.flyspeed

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
        keys = pygame.key.get_pressed()
        self.gravitycalc()

        self.moving = False

        if not cutscene:
            # key input

            if keys[pygame.K_p] and hax.active and hax.canfly:
                self.rect.y -= hax.flyspeed
            if keys[pygame.K_o]:
                x = 0
                for i in range(100):
                    x = abs(x)

                    if i < 25:
                        x += 4
                    elif 25 <= i < 50:
                        x -= 4
                    elif 50 <= i < 75:
                        x += 4
                    elif 75 <= i < 100:
                        x -= 4

                    y = 100 - x

                    if i >= 50:
                        x *= -1
                    if 25 <= i < 75:
                        y *= -1
                    particlesys.add(pos=plat.rect.center, vel=[x / 100, y / 100],
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

        self.changeaccel()

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
                    not 0 - particle['mass'] / 2 <= particle['pos'][0] <= width + particle['mass'] / 2 or \
                    not 0 - particle['mass'] / 2 <= particle['pos'][1] <= height + particle['mass'] / 2:
                self.particles.remove(particle)

        for particle in self.heldparticles:
            if particle['delay'] <= 0:
                particle.pop('delay')
                self.particles.append(dict(particle))
        self.heldparticles[:] = [particle for particle in self.heldparticles if 'delay' in particle]
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
    def __init__(self, rect):
        super().__init__()
        self.rect = rect


# surrounding check for a tile's connection to power
def power(rect) -> list[Direction]:
    powered = []

    tempsprite = Demo(rect)

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

    if len(uppower) > len(upblock):
        powered.append(Direction.up)
    if len(leftpower) > len(leftblock):
        powered.append(Direction.left)
    if len(downpower) > len(downblock):
        powered.append(Direction.down)
    if len(rightpower) > len(rightblock):
        powered.append(Direction.right)

    return powered


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
    global shadowsurf
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
                vortextiles.update(0)
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
                vortextiles.update(0)
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
                shadowsurf = pygame.Surface((width * 3, height * 3), pygame.SRCALPHA)
                pygame.draw.rect(shadowsurf, (*colors.DPURPLE, (2 * animtime - 180)), shadowsurf.get_rect())
                shake(1, int((animtime - 100) / 10), int((animtime - 100) / 10), 0, 0)
                screenrotation = (animtime - 109) * (90 / 130)
            if 180 <= animtime < 300:
                pygame.draw.rect(shadowsurf, (*colors.DPURPLE, 2 * 180 - 180), shadowsurf.get_rect())
                shake(1, int((animtime - 100) / 10), int((animtime - 100) / 10), 0, 0)
            if animtime == 300:
                animsound.play()
                animsound = pygame.mixer.Sound("assets/sfx/anims/anim1glitch4.ogg")
            if animtime == 360:
                vortextiles.update("assets/img/escape.png")
                vortextiles.update("assets/img/spawn.png", 1)
                shake(10, 5, 5, 0, 0)
                shadowsurf = pygame.Surface((screenwidth, screenheight), pygame.SRCALPHA)
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
def push(direction:Direction, saferects=None, *instigators:pygame.sprite.Sprite, weight=1):
    if direction not in Direction:
        raise ValueError("Direction required as input")
    saferects = iter(saferects)
    nextcollide = []
    for entity in instigators:
        collisiongroup = pygame.sprite.Group([s for s in solidtiles if s != entity and s.rect not in saferects])
        collided = pygame.sprite.spritecollide(entity, collisiongroup, False)
        for collision in collided:
            # noinspection PyUnresolvedReferences
            if hasattr(collision, "weight") and collision.weight <= weight or not hasattr(collision, "weight"):
                if collision.weight > 0:
                    nextcollide.append(collision)
                if direction == Direction.up:
                        collision.rect.bottom = entity.rect.top
                if direction == Direction.left:
                        collision.rect.right = entity.rect.left
                if direction == Direction.down:
                        collision.rect.top = entity.rect.bottom
                if direction == Direction.left:
                        collision.rect.left = entity.rect.right
                if callable(getattr(collision, "push", None)):
                    # noinspection PyUnresolvedReferences
                    collision.push(direction)
    if nextcollide:
        push(direction, None, *nextcollide)


# tile parent classes
class Tile(pygame.sprite.Sprite):
    def __init__(self, img, x=0, y=0, convert_alpha=False, rotate=0, weight=1):
        super().__init__()
        self.x = x
        self.y = y
        self.weight = weight
        self.mask = None
        if convert_alpha:
            self.image = pygame.image.load(img).convert_alpha()
            self.mask = pygame.mask.from_surface(self.image)
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
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

    def update(self):
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y

    def coverededge(self, direction:Direction=None):
        # this way it can be evaluated if direction is specified or iterated if not
        if pygame.sprite.spritecollide(self, solidtiles, False):
            return [True, True, True, True]

        if direction is None:
            coverededges = []

            self.rect.y -= 1
            coverededges.append(any([pygame.sprite.spritecollide(self, solidtiles, False), self.rect.top < 0]))
            self.rect.y += 1

            self.rect.x -= 1
            coverededges.append(any([pygame.sprite.spritecollide(self, solidtiles, False), self.rect.left < 0]))
            self.rect.x +=1

            self.rect.y += 1
            coverededges.append(any([pygame.sprite.spritecollide(self, solidtiles, False), self.rect.bottom > height]))
            self.rect.y -= 1

            self.rect.x += 1
            coverededges.append(any([pygame.sprite.spritecollide(self, solidtiles, False), self.rect.right > width]))
            self.rect.x -= 1

            return coverededges

        else:
            covered = None

            if direction == Direction.up:
                self.rect.y -= 1
                covered = any([pygame.sprite.spritecollide(self, solidtiles, False), self.rect.top < 0])
                self.rect.y += 1
            if direction == Direction.left:
                self.rect.x -= 1
                covered = any([pygame.sprite.spritecollide(self, solidtiles, False), self.rect.left < 0])
                self.rect.x += 1
            if direction == Direction.down:
                self.rect.y += 1
                covered = any([pygame.sprite.spritecollide(self, solidtiles, False), self.rect.bottom > height])
                self.rect.y -= 1
            if direction == Direction.right:
                self.rect.x += 1
                covered = any([pygame.sprite.spritecollide(self, solidtiles, False), self.rect.right > width])
                self.rect.x -= 1

            if covered is not None:
                return covered

            raise ValueError("Direction required as input")


class TempObj(pygame.sprite.Sprite):
    def __init__(self, img=None, x=0, y=0, convert_alpha=False, weight=-1):
        super().__init__()
        if img is not None:
            self.weight = weight
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
        self.direction = Direction.up
        self.speed = speed
        self.lastcollide = 1

    def update(self):
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y
            self.direction = Direction.up

        else:
            if power(self.rect):
                return "powered"

            if hax.active and hax.bumpyride:
                charcollide = pygame.sprite.collide_rect(self, plat)
            else:
                plat.rect.y += self.speed + 1
                charcollide = pygame.sprite.collide_rect(self, plat)
                plat.rect.y -= self.speed + 1

            upcanmove = leftcanmove = downcanmove = rightcanmove = False
            uptiles = lefttiles = downtiles = righttiles = None

            self.rect.y -= self.speed
            if pygame.sprite.spritecollide(self, circuittiles, False) and not \
                    (uptiles := pygame.sprite.spritecollide(self, elevcollidetiles, False)):
                upcanmove = True
            self.rect.y += self.speed

            self.rect.x -= self.speed
            if pygame.sprite.spritecollide(self, circuittiles, False) and not \
                    (lefttiles := pygame.sprite.spritecollide(self, elevcollidetiles, False)):
                leftcanmove = True
            self.rect.x += self.speed

            self.rect.y += self.speed
            if pygame.sprite.spritecollide(self, circuittiles, False) and not \
                    (downtiles := pygame.sprite.spritecollide(self, elevcollidetiles, False)):
                downcanmove = True
            self.rect.y -= self.speed

            self.rect.x += self.speed
            if pygame.sprite.spritecollide(self, circuittiles, False) and not \
                    (righttiles := pygame.sprite.spritecollide(self, elevcollidetiles, False)):
                rightcanmove = True
            self.rect.x -= self.speed

            # jumping right next to an elevator makes you fly (feature?)
            # but only when you jump on the left side while the elevator moves left
            # keeping bc funy
            if self.direction == Direction.up:
                if self.rect.top - self.speed < 0:
                    self.rect.top = 0
                    self.direction = Direction.left
                else:
                    if upcanmove:
                        self.rect.y -= self.speed
                    elif uptiles and uptiles[0].rect.bottom != self.rect.top:
                        self.rect.top = uptiles[0].rect.bottom
                        self.direction = Direction.left
                    else:
                        self.direction = Direction.left

                if charcollide or pygame.sprite.collide_rect(self, plat):
                    if upcanmove:
                        plat.rect.y -= self.speed
                    else:
                        plat.rect.y -= abs(self.rect.top - uptiles[0].rect.bottom)

            if self.direction == Direction.left:
                if self.rect.left - self.speed < 0:
                    self.rect.left = 0
                    self.direction = Direction.down
                else:
                    if leftcanmove:
                        self.rect.x -= self.speed
                    elif lefttiles and lefttiles[0].rect.right != self.rect.left:
                        self.rect.left = lefttiles[0].rect.right
                        self.direction = Direction.down
                    else:
                        self.direction = Direction.down

                if charcollide or pygame.sprite.collide_rect(self, plat):
                    plat.transportmomentum -= self.speed
                    if leftcanmove:
                        plat.rect.x -= self.speed
                    else:
                        plat.rect.x -= abs(self.rect.left - lefttiles[0].rect.right)

            if self.direction == Direction.down:
                if self.rect.bottom + self.speed > height:
                    self.rect.bottom = height
                    self.direction = Direction.right
                else:
                    if downcanmove:
                        self.rect.y += self.speed
                    elif downtiles and downtiles[0].rect.top != self.rect.bottom:
                        self.rect.bottom = downtiles[0].rect.top
                        self.direction = Direction.right
                    else:
                        self.direction = Direction.right

                # lastcollide stops the player from seemingly hopping after running off an elevator
                # the reason behind hopping is that the elevator moves down, but the player doesn't get
                # pulled down because he has ceased contact with the elevator
                if self.direction == Direction.down:
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
                            if downcanmove:
                                plat.rect.y += self.speed
                            else:
                                plat.rect.y += abs(self.rect.top - downtiles[0].rect.top)

            if self.direction == Direction.right:
                if self.rect.right + self.speed > width:
                    self.rect.right = width
                    self.direction = Direction.up
                else:
                    if rightcanmove:
                        self.rect.x += self.speed
                    elif righttiles and righttiles[0].rect.left != self.rect.right:
                        self.rect.right = uptiles[0].rect.left
                        self.direction = Direction.up
                    else:
                        self.direction = Direction.up

                if charcollide or pygame.sprite.collide_rect(self, plat):
                    plat.transportmomentum += self.speed
                    if rightcanmove:
                        plat.rect.x += self.speed
                    else:
                        plat.rect.x += abs(self.rect.right - righttiles[0].rect.left)

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
            # if you are still within the rect of the switch it won't be toggleable to prevent accidental toggles
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
            if self.ident == ident and ident >= 0:
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

                    selfpowered = power(self.rect)

                    if Direction.up in selfpowered:
                        projectiles.add(Bullet(self.rect.midbottom[0] - size / 8, self.rect.midbottom[1],
                                               Direction.down))
                    if Direction.left in selfpowered:
                        projectiles.add(Bullet(self.rect.midright[0], self.rect.midright[1] - size / 8,
                                               Direction.right))
                    if Direction.down in selfpowered:
                        projectiles.add(Bullet(self.rect.midtop[0] - size / 8, self.rect.midtop[1] - size / 4,
                                               Direction.up))
                    if Direction.right in selfpowered:
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
            plat.die("shot", self)
            self.kill()


class Light(Tile):
    corners, edges = shadowcasting.tiletopoly(pygame.sprite.Group([s for s in tiles if s not in lighttiles]))

    def __init__(self, x, y):
        super().__init__("assets/img/stealth/light.png", x, y)

    def update(self):
        selfpowered = power(self.rect)

        if Direction.up in selfpowered:
            lightingtiles.add(Lighting(self.rect.centerx, self.rect.centery, self.rect, Direction.down))
        if Direction.left in selfpowered:
            lightingtiles.add(Lighting(self.rect.centerx, self.rect.centery, self.rect, Direction.right))
        if Direction.down in selfpowered:
            lightingtiles.add(Lighting(self.rect.centerx, self.rect.centery, self.rect, Direction.up))
        if Direction.right in selfpowered:
            lightingtiles.add(Lighting(self.rect.centerx, self.rect.centery, self.rect, Direction.left))


class Lighting(TempObj):
    def __init__(self, x, y, hostrect, direction: Direction):
        super().__init__(x=x, y=y)
        self.hostrect = hostrect
        self.rect = pygame.rect.Rect((self.hostrect.centerx, self.hostrect.centery, 1, 1))
        self.rect.center = self.hostrect.center
        self.floatx = self.rect.x
        self.floaty = self.rect.y
        self.direction = direction
        self.vector = None
        self.maxrotate = None

        if self.direction == Direction.up:
            self.vector = pygame.math.Vector2(-1, -1).normalize()
            self.maxrotate = pygame.math.Vector2(1, -1)
        if self.direction == Direction.left:
            self.vector = pygame.math.Vector2(-1, 1).normalize()
            self.maxrotate = pygame.math.Vector2(-1, -1)
        if self.direction == Direction.down:
            self.vector = pygame.math.Vector2(1, 1).normalize()
            self.maxrotate = pygame.math.Vector2(-1, 1)
        if self.direction == Direction.right:
            self.vector = pygame.math.Vector2(1, -1).normalize()
            self.maxrotate = pygame.math.Vector2(1, 1)

    def update(self):
        while self.vector.angle_to(self.maxrotate) != 0:
            if (pygame.sprite.spritecollide(self, solidtiles, False) and not self.rect.colliderect(self.hostrect)) \
                    or not 0 <= self.rect.centerx <= width or not 0 <= self.rect.centery <= height:
                self.floatx -= self.vector.x
                self.floaty -= self.vector.y
                self.rect.topleft = self.floatx, self.floaty
                pygame.draw.line(shadowsurf, colors.DGRAY, self.hostrect.center, self.rect.center)
                self.rect.center = self.hostrect.center
                self.floatx, self.floaty = self.rect.topleft
                self.vector.rotate_ip(1)
                print("b")
            else:
                self.floatx += self.vector.x
                self.floaty += self.vector.y
                self.rect.topleft = self.floatx, self.floaty
                print(self.rect.x, self.rect.y)
            # print(self.rect)
            # print(self.vector.angle_to(self.maxrotate))
        print("done")



class Vortex(Tile):
    def __init__(self, x, y, ident, image, startimage):
        super().__init__(startimage, x, y)
        self.ident = ident
        self.rawimg = image

    def update(self, image="", ident=-1):
        if ident == self.ident and ident >= 0:
            glitch(self.rawimg)
            self.rawimg = glitchimg
            if image == "":
                self.image = pygame.image.load("assets/img/anims/glitchimg.png")
            else:
                self.image = pygame.image.load(image)


class Piston(Tile):
    def __init__(self, x, y, rotation=0):
        super().__init__("assets/img/piston.png", x, y, convert_alpha=True, rotate=rotation)
        self.rotation = rotation
        self.set = False
        self.child = None

    def update(self):
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y
            self.set = False
            if self.child is not None:
                self.child.kill()

        if not self.set:
            self.child = PistonRod(self.rect.x, self.rect.y, self.rect, self.rotation)
            self.child.add(pistonrodtiles, sprites, elevcollidetiles, bulletcollidetiles, solidtiles, collidetiles,
                           tiles)
            self.set = True

        if power(self.rect):
            self.child.update(True)
        else:
            self.child.update(False)


class PistonRod(Tile):
    def __init__(self, x, y, hostrect, rotation=0, speed=2):
        super().__init__("assets/img/pistonrod.png", x, y, convert_alpha=True, rotate=rotation)
        self.hostrect = hostrect
        self.rotation = rotation
        self.distance = 0
        self.speed = speed

    def update(self, active=False):
        # the parent handles killing child after player death
        if not plat.alive:
            pass

        if power(self.rect):
            active = True
        if self.rotation % 2 == 0:
            self.rect.x = self.hostrect.x
        else:
            self.rect.y = self.hostrect.y

        # one collision for self, one collision for host piston, one collision for the obstructive tile
        # TODO: add sound for breaking
        if self.distance != 32:
            if len(pygame.sprite.spritecollide(self, solidtiles, False)) >= 3:
                self.kill()
        elif len(pygame.sprite.spritecollide(self, solidtiles, False)) >= 2:
            self.kill()

        if active:
            if self.distance + self.speed <= 32:
                self.distance += self.speed
            else:
                self.distance = 32
        else:
            if self.distance - self.speed >= 0:
                self.distance -= self.speed
            else:
                self.distance = 0

        if self.direction == Direction.up:
            self.rect.y = self.hostrect.y - self.distance
        if self.direction == Direction.left:
            self.rect.x = self.hostrect.x - self.distance
        if self.direction == Direction.down:
            self.rect.y = self.hostrect.y + self.distance
        if self.direction == Direction.right:
            self.rect.x = self.hostrect.x + self.distance

        if pygame.sprite.spritecollide(self, solidtiles, False):
            push(self.direction, [self.hostrect, self.rect], self, weight=self.weight)


# refresh every frame
def redrawgamewindow():
    # ~10ms
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
    if lighttiles:
        # blend_rgba takes up A LOT of time (~23ms PER CALL)
        win.blit(shadowsurf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
    # ~1ms
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
        spawn = None
        stealth = False

        for tile in tiles:
            tile.kill()

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
        if lighttiles:
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

    if lavadeath := pygame.sprite.spritecollide(plat, lavatiles, False):
        plat.die("lava", lavadeath)
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

    # majority of resources are used here and down, above is ~0.1ms

    # ~5ms
    elevtiles.update()
    switchtiles.update()
    turrettiles.update()
    pistontiles.update()
    projectiles.update()
    plat.move()

    if stealth:
        lights.fill(colors.DGRAY)
        lightingtiles.update()
        lightingtiles.empty()
        lighttiles.update()

    # reset game window

    # ~1ms
    win = pygame.Surface((screenwidth / zoom, screenheight / zoom))
    win.fill(colors.BLACK)
    # ~11ms
    redrawgamewindow()
    # ~8ms
    screen.blit(pygame.transform.scale(pygame.transform.rotate(win, screenrotation),
                                       screen.get_size()), (0, 0))

    # print(timeit.default_timer() - start_time)
pygame.quit()
