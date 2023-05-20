import pygame
import pygame.font as fonts
from assets.data.lvldata import levels as levels
from assets.data.lvldata import leveldescs as leveldescs
from assets.data.lvldata import anims as anims
import assets.data.colors as colors
import assets.hax as hax
from assets.data.common import screenwidth, screenheight, width, height, size, Direction, Demo
import random
from glitch_this import ImageGlitcher
import timeit
from assets.data import shadowcasting as shca
from assets.data import tilegroups
from math import dist

# init ~1.7s
pygame.init()
hax.active = False
zoom = 1
screenshake = [0, 0]
shaketime = 0
shakeintensity = [0, 0]
shakedecay = [0, 0]
screenrotation = 0
mute = False
framerate = 60

screen = pygame.display.set_mode((screenwidth, screenheight), pygame.FULLSCREEN | pygame.SCALED)
win = pygame.Surface((screenwidth, screenheight))
shadowsurf = pygame.Surface((screenwidth, screenheight), pygame.HWSURFACE | pygame.SRCALPHA)

pygame.display.set_caption("Platman")
pygame.display.set_icon(pygame.image.load("assets/img/platterman.png").convert())
clock = pygame.time.Clock()
levelx = 0
levely = 0
spawn = None
invisiblespawn = False
glitcher = ImageGlitcher()
glitchimg = pygame.image.load("assets/img/escape.png").convert()

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
glasstiles = pygame.sprite.Group()
droppertiles = pygame.sprite.Group()
conveyortiles = pygame.sprite.Group()
conductortiles = pygame.sprite.Group()

# create special groups
spritesbg = pygame.sprite.Group()
sprites = pygame.sprite.Group()
sprites2 = pygame.sprite.Group()
projectiles = pygame.sprite.Group()

collidetiles = pygame.sprite.Group()
solidtiles = pygame.sprite.Group()
fallingtiles = pygame.sprite.Group()
tiles = pygame.sprite.Group()

guards = pygame.sprite.Group()

# load sound
ost = pygame.mixer.music
sfx = {
    'crush': pygame.mixer.Sound("assets/sfx/crush.ogg"),
    'melt': pygame.mixer.Sound("assets/sfx/melt.ogg"),
    'shoot': pygame.mixer.Sound("assets/sfx/shoot.ogg"),
    'hit': pygame.mixer.Sound("assets/sfx/hit.ogg"),
    'shotkill': pygame.mixer.Sound("assets/sfx/shotkill.ogg"),
    'press': pygame.mixer.Sound("assets/sfx/press.ogg")
}

animations = {
    'cutscene': False,
    'cutscenecount': 0,
    'animtime': 0,
    'animlive': False,
    'animsound': pygame.mixer.Sound("assets/sfx/anims/anim1glitch.ogg"),
}

# load misc
if hax.active:
    levelcount = hax.startlevel - 2
else:
    levelcount = 3
currentlvl = [0]
stealth = False


# define player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.momentum = 0
        self.baseaccel = 1
        self.airaccel = 0.3
        self.deaccel = 4
        self.airdeaccel = 0.5
        self.acceleration = 0
        self.vel = 10
        self.turnrate = 8
        self.transportmomentum = 0
        self.moving = False
        self.alive = True
        self.vertforce = 0
        self.gravity = 1.25
        self.jumpheight = 24
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
        self.image = pygame.image.load("assets/img/platterman.png").convert()
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
                self.momentum *= 2 / 3
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

        if not animations['cutscene']:
            # key input

            if keys[pygame.K_p] and hax.active and hax.canfly:
                self.rect.y -= hax.flyspeed
            if keys[pygame.K_o]:
                for repeat in range(10):
                    vec = pygame.math.Vector2(0, -1)
                    for i in range(360):
                        vec.rotate_ip(1)
                        particlesys.add(pos=plat.rect.center, vel=[vec.x, vec.y], mass=8, decay=0,
                                        gravity=0, color=(190, 195, 199), delay=i + 99 * repeat)

            if not ((keys[pygame.K_a] or keys[pygame.K_LEFT]) and (keys[pygame.K_d] or keys[pygame.K_RIGHT])):
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
                if self.weight >= tile1.weight:
                    push(Direction.right, self.rect, self, weight=self.weight)
                self.rect.right = tile1.rect.left
                self.momentum = 0
            elif self.momentum < 0:
                if self.weight >= tile1.weight:
                    push(Direction.left, self.rect, self, weight=self.weight)
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
                if self.weight >= tile1.weight:
                    push(Direction.down, self.rect, self, weight=self.weight)
                self.rect.bottom = tile1.rect.top
                self.vertforce = 0
            elif self.vertforce > 0:
                if self.weight >= tile1.weight:
                    push(Direction.up, self.rect, self, weight=self.weight)
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
        if collidedtiles:
            if not hax.active or not hax.noclip:
                if not mute:
                    sfx['crush'].play()
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
                    sfx['shotkill'].play()
            if cause == "lava":
                shake(45, 2, 2, 0, 0)
                if not mute:
                    sfx['melt'].play()
            if cause == "crushed":
                shake()
                for i in range(16):
                    particlesys.add(pos=self.rect.center, vel=[random.randint(-5, 5),
                                                               random.randint(-5, 5)], gravity=0, mass=15,
                                    decay=0.75, color=(190, 195, 199))
            if cause == "caught":
                shake(15)

            self.alive = False
            tiles.update()
            projectiles.update()
            guards.update()
            self.rect.x = spawn.x + size / 4
            self.rect.y = spawn.y + size / 2
            self.alive = True

    def shaded(self):
        if stealth and shadowsurf.get_at(self.rect.center) != (0, 0, 0, 255):
            return True
        return False


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
                del particle['delay']
                self.particles.append(dict(particle))
        self.heldparticles[:] = [particle for particle in self.heldparticles if 'delay' in particle]
        for particle in self.heldparticles:
            particle['delay'] -= 1


# surrounding check for a tile's connection to power
def power(rect: pygame.rect.Rect) -> list[Direction]:
    powered = []

    tempsprite = Demo(rect)

    tempsprite.rect.y -= 1
    uppower = pygame.sprite.spritecollide(tempsprite, [*rocktiles, *power.conductorcache], False)
    upblock = pygame.sprite.spritecollide(tempsprite, doortiles, False)
    tempsprite.rect.y += 1

    tempsprite.rect.x -= 1
    leftpower = pygame.sprite.spritecollide(tempsprite, [*rocktiles, *power.conductorcache], False)
    leftblock = pygame.sprite.spritecollide(tempsprite, doortiles, False)
    tempsprite.rect.x += 1

    tempsprite.rect.y += 1
    downpower = pygame.sprite.spritecollide(tempsprite, [*rocktiles, *power.conductorcache], False)
    downblock = pygame.sprite.spritecollide(tempsprite, doortiles, False)
    tempsprite.rect.y -= 1

    tempsprite.rect.x += 1
    rightpower = pygame.sprite.spritecollide(tempsprite, [*rocktiles, *power.conductorcache], False)
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


power.conductorcache = []


# image glitching
def glitch(image):
    global glitchimg
    random.seed(random.randint(1, 20000000))
    x = random.random()
    glitchimg = glitcher.glitch_image(src_img=image, glitch_amount=5, seed=x, color_offset=True, frames=1)
    glitchimg.save(r"assets\img\anims\glitchimg.png", format="PNG")


# anim system
def animate():
    global animations
    global shadowsurf
    global zoom
    global screenshake
    global screenrotation
    global mute

    if animations['animlive']:
        if animations['cutscenecount'] == 0:

            if animations['animtime'] == 0:
                plat.jumpheight = 1
                plat.gravity = 1
                plat.vel = 1
                mute = True
                animations['animsound'] = pygame.mixer.Sound("assets/sfx/anims/anim1glitch.ogg")
            if 20 < animations['animtime'] < 50:
                plat.moveleft()
            if animations['animtime'] == 55:
                vortextiles.update(0)
                shake(30, 5, 5, 1, 1)
                animations['animsound'].play()
                animations['animsound'] = pygame.mixer.Sound("assets/sfx/anims/anim1glitch2.ogg")
            if 55 <= animations['animtime'] < 60:
                plat.acceleration = 2
                plat.vel = 4
                plat.moveup()
                plat.moveright()
            if 60 <= animations['animtime'] < 90:
                plat.idle()
            if 90 <= animations['animtime'] < 240:
                vortextiles.update(0)
                if animations['animtime'] % 2 != 0:
                    plat.rect.x -= int((animations['animtime'] - 90) / 10)
            if animations['animtime'] == 110:
                animations['animsound'].play()
                animations['animsound'].play()
                animations['animsound'].play()
                animations['animsound'] = pygame.mixer.Sound("assets/sfx/anims/anim1glitch3.ogg")
            if 110 <= animations['animtime'] < 260:
                screenrotation = (animations['animtime'] - 109) * (90 / 150)
            if 180 <= animations['animtime'] < 260:
                zoom += 4.5 / 80
            if 110 <= animations['animtime'] < 180:
                plat.moveup()
                plat.moveright()
                shadowsurf = pygame.Surface((width * 3, height * 3), pygame.SRCALPHA)
                pygame.draw.rect(shadowsurf, (*colors.DPURPLE, (2 * animations['animtime'] - 180)),
                                 shadowsurf.get_rect())
                shake(1, int((animations['animtime'] - 100) / 10), int((animations['animtime'] - 100) / 10), 0, 0)
                screenrotation = (animations['animtime'] - 109) * (90 / 130)
            if 180 <= animations['animtime'] < 300:
                pygame.draw.rect(shadowsurf, (*colors.DPURPLE, 2 * 180 - 180), shadowsurf.get_rect())
                shake(1, int((animations['animtime'] - 100) / 10), int((animations['animtime'] - 100) / 10), 0, 0)
            if animations['animtime'] == 300:
                animations['animsound'].play()
                animations['animsound'] = pygame.mixer.Sound("assets/sfx/anims/anim1glitch4.ogg")
            if animations['animtime'] == 360:
                vortextiles.update("assets/img/escape.png")
                vortextiles.update("assets/img/spawn.png", 1)
                shake(10, 5, 5, 0, 0)
                shadowsurf = pygame.Surface((screenwidth, screenheight), pygame.SRCALPHA)
                animations['animsound'].play()
            if 420 <= animations['animtime'] < 570:
                zoom -= 15.5 / 150
            if 420 <= animations['animtime'] < 480:
                screenrotation -= 1.5
            if animations['animtime'] == 510:
                mute = False
            if animations['animtime'] == 920:
                animations['animlive'] = False

        animations['animtime'] += 1

    else:
        animations['cutscene'] = False
        animations['cutscenecount'] += 1
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
def push(direction: Direction, saferects=None, *instigators: pygame.sprite.Sprite, weight=None):
    if direction not in Direction:
        raise ValueError("Direction required as input")
    saferects = iter(saferects) if saferects is not None else []
    nextcollide = []
    for entity in instigators:
        collisiongroup = pygame.sprite.Group([s for s in solidtiles if s != entity and s.rect not in saferects])
        collided = pygame.sprite.spritecollide(entity, collisiongroup, False)
        for collision in collided:
            nextcollide.append(collision)
            # noinspection PyUnresolvedReferences
            if (hasattr(collision, "weight") and collision.weight <=
                    (weight if weight is not None else entity.weight)) or not hasattr(collision, "weight"):
                if direction == Direction.up:
                    collision.rect.bottom = entity.rect.top
                if direction == Direction.left:
                    collision.rect.right = entity.rect.left
                if direction == Direction.down:
                    collision.rect.top = entity.rect.bottom
                if direction == Direction.right:
                    collision.rect.left = entity.rect.right
                if callable(getattr(collision, "push", None)):
                    collision.push(direction)
            else:
                if direction == Direction.up:
                    entity.rect.top = collision.rect.bottom
                if direction == Direction.left:
                    entity.rect.left = collision.rect.right
                if direction == Direction.down:
                    entity.rect.bottom = collision.rect.top
                if direction == Direction.right:
                    entity.rect.right = collision.rect.left
                if callable(getattr(entity, "push", None)):
                    entity.push(direction)

    if nextcollide:
        push(direction, None, *nextcollide)


def boundscheck(rect: pygame.rect.Rect) -> bool:
    if rect.left < 0 or rect.right > width or rect.top < 0 or rect.right > height:
        return False
    return True


# tile parent classes
class Tile(pygame.sprite.Sprite):
    def __init__(self, img, x=0, y=0, convert_alpha=False, rotate=0, weight=1, flip=False):
        super().__init__()
        self.x = x
        self.y = y
        self.weight = weight  # <0 pushable, <1 falling
        self.shaded = False
        self.image = None
        self.mask = None
        if convert_alpha:
            self.image = pygame.image.load(img).convert_alpha()
            self.mask = pygame.mask.from_surface(self.image)
        else:
            self.image = pygame.image.load(img).convert()
        self.image = pygame.transform.rotate(self.image, rotate * 90)

        if rotate == 0:
            self.direction = Direction.up
        if rotate == 1:
            self.direction = Direction.left
        if rotate == 2:
            self.direction = Direction.down
        if rotate == 3:
            self.direction = Direction.right

        if flip:
            self.image = pygame.transform.flip(self.image, True, False)

        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

        self.vertforce = 0
        self.gravity = plat.gravity
        self.tvel = plat.tvel
        self.grounded = False
        self.transportmomentum = 0

    def update(self):
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y
            return

        if self.weight < 1:
            self.gravitycalc()

    def push(self, direction: Direction):
        pass

    def populategroups(self):
        tiles.add(self)
        if hasattr(tilegroups, self.__class__.__name__):
            try:
                self.add(*[eval(s) for s in eval(f"tilegroups.{self.__class__.__name__}")])
            except RuntimeError:
                raise RuntimeError(f"populategroups() didn't work for {self.__class__.__name__}")
        else:
            raise NotImplementedError(f"Class '{self.__class__.__name__}' not defined in tilegroups.py")

    def coverededge(self, direction: Direction = None):
        # this way it can be (evaluated if direction is specified else iterated)
        if pygame.sprite.spritecollide(self, [s for s in solidtiles if s != self], False):
            return {
                'up': True,
                'left': True,
                'down': True,
                'right': True,
            }

        if direction is None:
            coverededges = {}
            tempgroup = [s for s in solidtiles if s != self]

            self.rect.y -= 1
            coverededges['up'] = any([pygame.sprite.spritecollide(self, tempgroup, False), self.rect.top < 0])
            self.rect.y += 1

            self.rect.x -= 1
            coverededges['left'] = any([pygame.sprite.spritecollide(self, tempgroup, False), self.rect.left < 0])
            self.rect.x += 1

            self.rect.y += 1
            coverededges['down'] = any([pygame.sprite.spritecollide(self, tempgroup, False), self.rect.bottom > height])
            self.rect.y -= 1

            self.rect.x += 1
            coverededges['right'] = any([pygame.sprite.spritecollide(self, tempgroup, False), self.rect.right > width])
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

    def coveredcorner(self, coverededges=None):
        if coverededges is None:
            coverededges = [True, True, True, True]

        tempgroup = [s for s in tiles if s not in solidtiles and s != self]
        coveredcorners = {}

        if coverededges['up'] and coverededges['left']:
            self.rect.x -= 1
            self.rect.y -= 1
            coveredcorners['upleft'] = any([not pygame.sprite.spritecollide(self, tempgroup, False),
                                            self.rect.top < 0, self.rect.left < 0])
            self.rect.x += 1
            self.rect.y += 1
        else:
            coveredcorners['upleft'] = False

        if coverededges['left'] and coverededges['down']:
            self.rect.x -= 1
            self.rect.y += 1
            coveredcorners['downleft'] = (any([not pygame.sprite.spritecollide(self, tempgroup, False),
                                               self.rect.bottom > height, self.rect.left < 0]))
            self.rect.x += 1
            self.rect.y -= 1
        else:
            coveredcorners['downleft'] = False

        if coverededges['down'] and coverededges['right']:
            self.rect.x += 1
            self.rect.y += 1
            coveredcorners['downright'] = (any([not pygame.sprite.spritecollide(self, tempgroup, False),
                                                self.rect.bottom > height, self.rect.right > width]))
            self.rect.x -= 1
            self.rect.y -= 1
        else:
            coveredcorners['downright'] = False

        if coverededges['right'] and coverededges['up']:
            self.rect.x += 1
            self.rect.y -= 1
            coveredcorners['upright'] = (any([not pygame.sprite.spritecollide(self, tempgroup, False),
                                              self.rect.top < 0, self.rect.right > width]))
            self.rect.x -= 1
            self.rect.y += 1
        else:
            coveredcorners['upright'] = False

        return coveredcorners

    def shaded(self):
        if stealth and shadowsurf.get_at(self.rect.center) != (0, 0, 0, 255):
            return True
        return False

    def gravitycalc(self):
        if self.weight >= 1:
            return

        selfcollidetiles = [s for s in collidetiles if s != self]
        self.rect.y += 2
        grounded = pygame.sprite.spritecollide(self, selfcollidetiles, False)
        self.rect.y -= 2

        if grounded or self.rect.bottom >= height:
            if not self.grounded:
                self.grounded = True

        else:
            self.grounded = False
            if self.vertforce - self.gravity < -self.tvel:
                self.vertforce = -self.tvel
            else:
                self.vertforce -= self.gravity

        self.rect.y -= self.vertforce
        collidedtiles = pygame.sprite.spritecollide(self, selfcollidetiles, False)

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
        if collidedtiles:
            if not hax.active or not hax.noclip:
                if not mute:
                    sfx['crush'].play()


class TempObj(pygame.sprite.Sprite):
    def __init__(self, img=None, x=0, y=0, convert_alpha=False, weight=-1):
        super().__init__()
        if img is not None:
            self.weight = weight
            if convert_alpha:
                self.image = pygame.image.load(img).convert_alpha()
                self.mask = pygame.mask.from_surface(self.image)
            else:
                self.image = pygame.image.load(img).convert()
            self.rect = self.image.get_rect()
            self.rect.x, self.rect.y = x, y

    def update(self):
        if not plat.alive:
            self.kill()
            return

    def populategroups(self):
        projectiles.add(self)
        if hasattr(tilegroups, self.__class__.__name__):
            try:
                self.add(*[eval(s) for s in eval(f"tilegroups.{self.__class__.__name__}") if s in globals()])
            except RuntimeError:
                pass
        else:
            raise NotImplementedError(f"Class '{self.__class__.__name__}' not defined in tilegroups.py")

    def coverededge(self):
        if hasattr(self, 'rect') and pygame.sprite.spritecollide(self, [s for s in solidtiles if s != self], False):
            return {
                'up': True,
                'left': True,
                'down': True,
                'right': True,
            }
        return {
            'up': False,
            'left': False,
            'down': False,
            'right': False,
        }

    def coveredcorner(self, dummyval=None):
        if hasattr(self, 'rect') and dummyval is None:
            return {
                'upleft': True,
                'downleft': True,
                'downright': True,
                'upright': True,
            }
        return {
            'upleft': True,
            'downleft': True,
            'downright': True,
            'upright': True,
        }


class Guard(pygame.sprite.Sprite):
    awareness = {
        'reset': None,
        'observing': pygame.image.load("assets/img/stealth/eye.png"),
        'cautious': pygame.image.load("assets/img/stealth/questionmark.png"),
        'alert': pygame.image.load("assets/img/stealth/exclamationmark.png"),
    }

    def __init__(self, x, y, target: pygame.sprite.Sprite = None, image="assets/img/stealth/guard.png",
                 facing=Direction.left, speed: list = None, path: list[shca.Coord] = None):
        super().__init__()
        self.x = x
        self.y = y
        self.imageL = pygame.image.load(image).convert()
        self.imageR = pygame.transform.flip(self.imageL, True, False)
        self.rect = self.imageL.get_rect()
        self.rect.x, self.rect.y = x, y
        self.defaultfacing = facing
        if isinstance(facing, str):
            if facing.lower() == 'l':
                self.defaultfacing = Direction.left
            elif facing.lower() == 'r':
                self.defaultfacing = Direction.right
            else:
                raise TypeError("facing must be a Direction, 'l', or 'r'")
        self.facing = self.defaultfacing
        self.grounded = False
        self.vertforce = 0
        self.gravity = 1.25
        self.tvel = 30
        self.jumpheight = 8
        self.momentum = 0
        self.speed = speed
        if speed is None:
            self.speed = [5, 10]
        self.path = path
        # if path is not None:
        #     self.path = [Demo(pygame.rect.Rect(*s, 1, 1)) for s in path]
        self.grace = 1.0
        self.alert = -self.grace
        self.visiondecay = 0.1
        self.darkmod = 2
        if path is None:
            self.visiondecay /= 2
        self.target = target
        if target is None:
            self.target = plat
        self.lastseenpos: shca.Coord = None
        self.timesinceseen = -1
        self.targetnode = None
        self.nodeindex = -1
        self.lastpathpos = None
        self.reverse = False
        self.icon = {
            'icon': "",
            'pos': 0,
            'rateofchange': 4,
        }

    def update(self):
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y
            self.momentum = self.vertforce = 0
            self.facing = self.defaultfacing
            self.alert = -self.grace
            self.lastseenpos: shca.Coord = None
            self.timesinceseen = -1
            self.targetnode = None
            self.nodeindex = -1
            self.lastpathpos = None
            self.reverse = False
            self.icon = {
                'icon': "",
                'pos': 0,
                'rateofchange': 4,
            }
            return

        self.pathfind()
        self.observe()

        self.gravitycalc()

    def pathfind(self):
        if self.alert <= 0:
            if self.path is None and self.lastpathpos is None:
                if self.alert == -self.grace:
                    self.popup('observing')
                    self.timesinceseen = -1
                return

            if self.alert == -self.grace:
                self.popup('reset')
                self.timesinceseen = -1

            if self.path is None:
                pass
            elif self.lastpathpos is None:
                for i in range(len(self.path) - 1):
                    if shca.segmentintersect((self.path[i], self.path[i + 1]),
                                             (self.rect.midtop, self.rect.midbottom)) or \
                            shca.segmentintersect((self.path[i], self.path[i + 1]),
                                                  (self.rect.midleft, self.rect.midright)):
                        if self.path[i][0] < self.rect.centerx or self.path[i][0] > self.rect.centerx:
                            self.targetnode = self.path[i]
                            self.nodeindex = i
                            self.lastpathpos = self.rect.center
                            self.reverse = True
                        elif self.path[i + 1][0] < self.rect.centerx or self.path[i + 1][0] > self.rect.centerx:
                            self.targetnode = self.path[i + 1]
                            self.nodeindex = i + 1
                            self.lastpathpos = self.rect.center
                            self.reverse = False
                        break
            elif self.rect.collidepoint(*self.targetnode):
                if self.nodeindex == 0 or self.nodeindex == len(self.path) - 1:
                    self.reverse = not self.reverse
                    if len(self.path) == 1:
                        self.path = None
                        return
                    elif len(self.path) == 2:
                        self.nodeindex = 0 if self.nodeindex != 0 else 1
                    else:
                        self.nodeindex = max(min(self.nodeindex, len(self.path) - 2), 1)
                    self.targetnode = self.path[self.nodeindex]
                else:
                    self.nodeindex += -1 if self.reverse else 1
                    self.targetnode = self.path[self.nodeindex]

            if self.targetnode:
                self.facing = Direction.left if self.targetnode[0] < self.rect.centerx else Direction.right
            self.momentum += -self.speed[0] if self.facing == Direction.left else self.speed[0]
        else:
            if self.rect.colliderect(self.target):
                if plat == self.target:
                    plat.die("caught", self)
                    return

            if self.rect.collidepoint(*self.lastseenpos) or self.timesinceseen >= 150:
                self.alert = -self.grace
                self.timesinceseen = -1
                self.lastseenpos = None
                self.targetnode = self.lastpathpos
                return

            self.facing = Direction.left if self.lastseenpos[0] < self.rect.centerx else Direction.right
            if 0 < self.alert < 1:
                self.momentum += -self.speed[0] if self.facing == Direction.left else self.speed[0]
            elif self.alert >= 1:
                self.momentum += -self.speed[1] if self.facing == Direction.left else self.speed[1]

    def observe(self):
        for edge in Light.polycache[1]:
            if shca.segmentintersect((self.rect.center, self.target.rect.center), edge):
                self.timesinceseen += 1 if self.timesinceseen > -1 else 0
                break
        else:
            if shca.checkvisible(self.rect.center, self.target.rect.center, self.facing):
                mod = self.darkmod if self.target.shaded() else 1
                if (amt := 0.5 * (1 - self.visiondecay * mod *
                                  (dist(self.rect.center, self.target.rect.center) // 32))) > 0:
                    self.lastseenpos = self.target.rect.center
                    self.timesinceseen = 0
                    self.alert += amt

        if -self.grace < self.alert < 1:
            self.popup('cautious')
        elif self.alert >= 1:
            self.popup('alert')

        if -self.grace < self.alert <= 0 and self.timesinceseen > 0:
            self.alert = max(self.alert - 1 / 60, -self.grace)

    def gravitycalc(self):
        self.rect.y += 2
        grounded = pygame.sprite.spritecollide(self, collidetiles, False)
        self.rect.y -= 2

        if grounded or self.rect.bottom >= height:
            self.grounded = True
        else:
            self.grounded = False

        if self.vertforce - self.gravity < -self.tvel:
            self.vertforce = -self.tvel
        else:
            self.vertforce -= self.gravity

        self.rect.x += self.momentum
        collidedtiles = pygame.sprite.spritecollide(self, collidetiles, False)
        didcollide = any(collidedtiles)

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
                self.rect.right = tile1.rect.left
        if self.rect.bottom > height:
            self.rect.bottom = height
            self.vertforce = 0
        if self.rect.top < 0:
            self.rect.top = 0
            self.vertforce = 0

        if self.grounded:
            if didcollide:
                self.jump()
            elif self.alert >= 1 and self.target.rect.bottom < self.rect.top:
                self.jump()
            elif self.lastseenpos and self.lastseenpos[1] < self.rect.top \
                    and self.rect.left <= self.lastseenpos[0] <= self.rect.right:
                self.jump()

    def jump(self):
        self.vertforce += self.jumpheight
        self.rect.y -= 1

    def popup(self, icon: str = None, draw=False):
        if icon:
            if self.icon['icon'] == Guard.awareness[icon]:
                pass
            else:
                self.icon['icon'] = Guard.awareness[icon]
                self.icon['pos'] = 0
                self.icon['rateofchange'] = 4
        if draw:
            if self.icon['icon']:
                if self.icon['pos'] >= 0:
                    self.icon['pos'] += self.icon['rateofchange']
                    self.icon['rateofchange'] -= 0.5
                else:
                    self.icon['pos'] = -1
                    self.icon['rateofchange'] = 0
                win.blit(self.icon['icon'], (self.rect.x, self.rect.y - 48 - self.icon['pos']))


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
            self.image = pygame.image.load("assets/img/space.png").convert()
            self.rect = self.image.get_rect()


class Lava(Tile):
    def __init__(self, x, y):
        super().__init__("assets/img/lava.png", x, y)


class Esc(Tile):
    def __init__(self, x, y):
        super().__init__("assets/img/escape.png", x, y)


class Elev(Tile):
    collidetiles = pygame.sprite.Group()

    def __init__(self, x, y, speed=2):
        super().__init__("assets/img/elevator.png", x, y)
        self.direction = Direction.up
        self.speed = speed
        self.lastcollide = 1

    def update(self):
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y
            self.direction = Direction.up
            return

        if power(self.rect):
            return f"{self} powered"

        upcanmove = leftcanmove = downcanmove = rightcanmove = False
        uptiles = lefttiles = downtiles = righttiles = None
        localcollidetiles = [s for s in Elev.collidetiles if s != self]

        self.rect.y -= self.speed
        if pygame.sprite.spritecollide(self, circuittiles, False) and not \
                (uptiles := pygame.sprite.spritecollide(self, localcollidetiles, False)):
            upcanmove = True
        self.rect.y += self.speed

        self.rect.x -= self.speed
        if pygame.sprite.spritecollide(self, circuittiles, False) and not \
                (lefttiles := pygame.sprite.spritecollide(self, localcollidetiles, False)):
            leftcanmove = True
        self.rect.x += self.speed

        self.rect.y += self.speed
        if pygame.sprite.spritecollide(self, circuittiles, False) and not \
                (downtiles := pygame.sprite.spritecollide(self, localcollidetiles, False)):
            downcanmove = True
        self.rect.y -= self.speed

        self.rect.x += self.speed
        if pygame.sprite.spritecollide(self, circuittiles, False) and not \
                (righttiles := pygame.sprite.spritecollide(self, localcollidetiles, False)):
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

            if followers := pygame.sprite.spritecollide(self, [plat, *fallingtiles], False):
                for follower in followers:
                    if upcanmove:
                        follower.rect.y -= self.speed
                    else:
                        follower.rect.y -= abs(self.rect.top - uptiles[0].rect.bottom)

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

            if followers := pygame.sprite.spritecollide(self, [plat, *fallingtiles], False):
                for follower in followers:
                    follower.transportmomentum -= self.speed
                    if leftcanmove:
                        follower.rect.x -= self.speed
                    else:
                        follower.rect.x -= abs(self.rect.left - lefttiles[0].rect.right)

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
                if followers := pygame.sprite.spritecollide(self, [plat, *fallingtiles], False):
                    collision = True
                    for follower in followers:
                        if follower.grounded:
                            if follower.rect.left < self.rect.left:
                                self.rect.x -= 2
                                collidedtiles = pygame.sprite.spritecollide(self, collidetiles, False)
                                self.rect.x += 2
                                for tile1 in collidedtiles:
                                    if tile1.rect.top <= self.rect.top:
                                        collision = False
                                        break
                            if follower.rect.right > self.rect.right:
                                self.rect.x += 2
                                collidedtiles = pygame.sprite.spritecollide(self, collidetiles, False)
                                self.rect.x -= 2
                                for tile1 in collidedtiles:
                                    if tile1.rect.top <= self.rect.top:
                                        collision = False
                                        break
                        if collision:
                            if downcanmove:
                                follower.rect.y += self.speed
                            else:
                                follower.rect.y += abs(self.rect.top - downtiles[0].rect.top)
                        follower.vertforce -= self.speed

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

            if followers := pygame.sprite.spritecollide(self, [plat, *fallingtiles], False):
                for follower in followers:
                    follower.transportmomentum += self.speed
                    if rightcanmove:
                        follower.rect.x += self.speed
                    else:
                        follower.rect.x += abs(self.rect.right - righttiles[0].rect.left)


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
                sfx['press'].play()
                self.image = pygame.image.load("assets/img/switch2.png").convert_alpha()
                self.mask = pygame.mask.from_surface(self.image)
                doortiles.update(self.ident)
                print(f"Signal: ID {self.ident}")

        else:
            # if you are still within the rect of the Switch it won't be toggleable (to prevent accidental toggles)
            if not pygame.sprite.collide_rect(self, plat):
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
            self.populategroups()

        else:
            if self.ident == ident and ident >= 0:
                if sprites2.has(self):
                    self.kill()
                    self.add(doortiles, tiles)
                else:
                    self.populategroups()


class Rock(Tile):
    def __init__(self, x, y):
        super().__init__("assets/img/hotrock.png", x, y, weight=-1)


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

                    powered = power(self.rect)

                    if Direction.up in powered:
                        projectiles.add(Bullet(self.rect.midbottom[0] - size / 8, self.rect.midbottom[1],
                                               Direction.down))
                    if Direction.left in powered:
                        projectiles.add(Bullet(self.rect.midright[0], self.rect.midright[1] - size / 8,
                                               Direction.right))
                    if Direction.down in powered:
                        projectiles.add(Bullet(self.rect.midtop[0] - size / 8, self.rect.midtop[1] - size / 4,
                                               Direction.up))
                    if Direction.right in powered:
                        projectiles.add(Bullet(self.rect.midleft[0] - size / 4, self.rect.midleft[1] - size / 8,
                                               Direction.left))
                    self.cooldown = self.firerate
                    if not mute:
                        sfx['shoot'].play()


class Bullet(TempObj):
    def __init__(self, x, y, direction, speed=5):
        super().__init__("assets/img/bullet.png", x, y)
        self.rect.x, self.rect.y = x, y
        self.direction = direction
        self.speed = speed
        self.set = False

    def update(self):
        if not plat.alive:
            self.kill()
            return

        if not self.set:
            self.populategroups()
            self.set = True

        if self.direction == Direction.up:
            self.rect.y -= self.speed
        if self.direction == Direction.left:
            self.rect.x -= self.speed
        if self.direction == Direction.down:
            self.rect.y += self.speed
        if self.direction == Direction.right:
            self.rect.x += self.speed

        collide = pygame.sprite.spritecollide(self, [s for s in solidtiles if s != self], False)
        charcollide = pygame.sprite.collide_rect(self, plat)
        if collide or boundscheck(self.rect):
            self.kill()
            if not mute:
                sfx['hit'].play()
        if charcollide:
            plat.die("shot", self)
            self.kill()


class Light(Tile):
    polycache: list[list[shca.Coord], list[shca.Line]]

    def __init__(self, x, y):
        super().__init__("assets/img/stealth/light.png", x, y)
        self.lighting: list[Lighting, Lighting, Lighting, Lighting] = [None, None, None, None]

    def push(self, direction: Direction):
        for lighting in self.lighting:
            lighting.kill()
        self.lighting = [None, None, None, None]

    def update(self):
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y
            return

        Light.polycache = shca.tiletopoly(solidtiles)
        powered = power(self.rect)

        if Direction.up in powered:
            self.lighting[0] = Lighting(self.rect.centerx, self.rect.centery, self.rect, Direction.down)
            lightingtiles.add(self.lighting[0])
        elif self.lighting[0]:
            self.lighting[0].kill()
            self.lighting[0] = None

        if Direction.left in powered:
            self.lighting[1] = Lighting(self.rect.centerx, self.rect.centery, self.rect, Direction.right)
            lightingtiles.add(self.lighting[1])
        elif self.lighting[1]:
            self.lighting[1].kill()
            self.lighting[1] = None

        if Direction.down in powered:
            self.lighting[2] = Lighting(self.rect.centerx, self.rect.centery, self.rect, Direction.up)
            lightingtiles.add(self.lighting[2])
        elif self.lighting[2]:
            self.lighting[2].kill()
            self.lighting[2] = None

        if Direction.right in powered:
            self.lighting[3] = Lighting(self.rect.centerx, self.rect.centery, self.rect, Direction.left)
            lightingtiles.add(self.lighting[3])
        elif self.lighting[3]:
            self.lighting[3].kill()
            self.lighting[3] = None


class Lighting(TempObj):
    def __init__(self, x, y, hostrect: pygame.rect.Rect, direction: Direction):
        super().__init__(x=x, y=y)
        self.hostrect = hostrect
        self.rect = pygame.rect.Rect((self.hostrect.centerx, self.hostrect.centery, 1, 1))
        self.rect.center = self.hostrect.center
        self.direction = direction
        self.polycache = list[list[shca.Coord], list[shca.Line]]
        self.visiblepolycache: list[list[shca.Coord], list[shca.Line]] = []

    def fillpolycaches(self):
        self.polycache = [[s for s in Light.polycache[0] if not (
                self.hostrect.left - 1 <= s[0] <= self.hostrect.right + 1 and
                self.hostrect.top - 1 <= s[1] <= self.hostrect.bottom + 1)],

                          [s for s in Light.polycache[1] if not (
                                  self.hostrect.left <= s[0][0] <= self.hostrect.right and
                                  self.hostrect.top <= s[0][1] <= self.hostrect.bottom and
                                  self.hostrect.left <= s[1][0] <= self.hostrect.right and
                                  self.hostrect.top <= s[1][1] <= self.hostrect.bottom)]]
        self.visiblepolycache = [
            shca.rayvisiblecorners(solidtiles, self.hostrect, self.hostrect.center,
                                   self.polycache[0], self.polycache[1], self.direction),
        ]
        self.visiblepolycache.append(shca.visibleedges(self.visiblepolycache[0]))

    def update(self):
        if not plat.alive:
            pass

        self.fillpolycaches()

        for corner in self.visiblepolycache[0]:
            pygame.draw.line(shadowsurf, colors.BLACK, self.hostrect.center, corner)

        for line in self.visiblepolycache[1]:
            # pygame.draw.line(shadowsurf, colors.LGRAY, *line, 2)
            pygame.draw.polygon(shadowsurf, colors.BLACK, (*line, self.hostrect.center))

        pygame.draw.rect(shadowsurf, colors.DGRAY, self.hostrect)


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
                self.image = pygame.image.load("assets/img/anims/glitchimg.png").convert()
            else:
                self.image = pygame.image.load(image).convert()


class Piston(Tile):
    def __init__(self, x, y, rotation=0):
        super().__init__("assets/img/piston.png", x, y, convert_alpha=True, rotate=rotation)
        self.rotation = rotation
        self.child = None

    def update(self):
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y
            if self.child is not None:
                self.child.kill()
                self.child = None

        if self.child is None or not self.child.groups():
            self.child = PistonRod(self.rect.x, self.rect.y, self.rect, self.rotation)
            self.child.populategroups()

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

    def push(self, direction: Direction):
        if direction == Direction.up:
            if self.direction == Direction.down:
                self.distance = abs(self.rect.y - self.hostrect.y)
        if direction == Direction.left:
            if self.direction == Direction.right:
                self.distance = abs(self.rect.x - self.hostrect.x)
        if direction == Direction.down:
            if self.direction == Direction.up:
                self.distance = abs(self.rect.y - self.hostrect.y)
        if direction == Direction.right:
            if self.direction == Direction.left:
                self.distance = abs(self.rect.x - self.hostrect.x)


class Diamond(Tile):
    def __init__(self, x, y):
        super().__init__("assets/img/stealth/diamond.png", x, y, True)


class Glass(Tile):
    def __init__(self, x, y):
        super().__init__("assets/img/stealth/glass.png", x, y)


class Dropper(Tile):
    def __init__(self, x, y, ident, rotation=0):
        super().__init__("assets/img/dropper.png", x, y, rotate=rotation)
        self.ident = ident
        self.child = None

    def update(self, ident=-1):
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y
            if self.child is not None:
                self.child.kill()
                self.child = None

        # TODO: add sound for dropping
        if (self.child is None or not self.child.groups()) and (power(self.rect) or self.ident == ident):
            if self.direction == Direction.up:
                self.child = Droplet(self.rect.midbottom[0] - size / 8, self.rect.midbottom[1])
            if self.direction == Direction.left:
                self.child = Droplet(self.rect.midright[0], self.rect.midright[1] - size / 8)
            if self.direction == Direction.down:
                self.child = Droplet(self.rect.midtop[0] - size / 8, self.rect.midtop[1] - size / 4)
            if self.direction == Direction.right:
                self.child = Droplet(self.rect.midleft[0] - size / 4, self.rect.midleft[1] - size / 8)
            projectiles.add(self.child)


class Droplet(Tile):
    def __init__(self, x, y):
        super().__init__("assets/img/droplet.png", x, y, weight=-1)


class Conveyor(Tile):
    def __init__(self, x, y, facing: Direction = Direction.left, speed=2):
        super().__init__("assets/img/conveyor", x, y, flip=False if facing == Direction.left else True)
        self.facing = facing
        self.speed = -speed if facing == Direction.left else speed

    def update(self):
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y

        if not power(self.rect):
            return

        self.rect.y -= 2
        collisions = pygame.sprite.spritecollide(self, [plat, *fallingtiles], False)
        self.rect.y += 2

        for collision in collisions:
            collision.rect.x += self.speed
            if collision is plat:
                collision.transportmomentum += self.speed


class Conductor(Tile):
    def __init__(self, x, y):
        super().__init__("assets/img/conductor.png", x, y, weight=-1)
        self.on = False

    def update(self):
        self.on = True if power(self.rect) else False


# refresh every frame
def redrawgamewindow():
    # ~10ms

    # spritesbg -> sprites -> sprites2 -> projectiles -> particles
    for sprite in spritesbg:
        win.blit(sprite.image, (sprite.rect.x + screenshake[0], sprite.rect.y + screenshake[1]))
    for sprite in sprites:
        win.blit(sprite.image, (sprite.rect.x + screenshake[0], sprite.rect.y + screenshake[1]))
    for sprite in sprites2:
        win.blit(sprite.image, (sprite.rect.x + screenshake[0], sprite.rect.y + screenshake[1]))
    for sprite in projectiles:
        win.blit(sprite.image, (sprite.rect.x + screenshake[0], sprite.rect.y + screenshake[1]))
    for sprite in guards:
        win.blit(sprite.imageL if sprite.facing == Direction.left else sprite.imageR,
                 (sprite.rect.x + screenshake[0], sprite.rect.y + screenshake[1]))
        sprite.popup(draw=True)
    if particlesys.particles or particlesys.heldparticles:
        particlesys.run("square")
    win.blit(leveltext, (4, 1024))
    win.blit(plat.image, (plat.rect.x + screenshake[0], plat.rect.y + screenshake[1]))
    for sprite in vortextiles:
        win.blit(sprite.image, (sprite.rect.x + screenshake[0], sprite.rect.y + screenshake[1]))
    if lighttiles:
        win.blit(shadowsurf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        # for sprite in lightingtiles:
        #     for coord in sprite.visiblepolycache[0]:
        #         pygame.draw.circle(win, colors.RED, coord, 1)
        #     for coord in Light.polycache[0]:
        #         pygame.draw.line(win, colors.RED, sprite.rect.center, coord)
        # for coord in Light.polycache[0]:
        #     pygame.draw.circle(win, colors.RED, coord, 1)

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
# TODO: grappling hook, moving turrets, multi-level stages
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
        if not animations['cutscene']:
            currentlvl = levels[levelcount]
            leveltext = font1.render(f"Level {levelcount + 1} : {leveldescs[levelcount]}", False, colors.WHITE)
        else:
            currentlvl = anims[animations['cutscenecount']]
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
                if tile == 10:
                    turrettiles.add(Turret(levelx, levely))
                if tile == 11:
                    lighttiles.add(Light(levelx, levely))
                if tile == 14:
                    guards.add(Guard(levelx, levely))
                if type(tile) == list:
                    if tile[0] == 1:
                        if tile[1] == 0:
                            glasstiles.add(Glass(levelx, levely))
                    if tile[0] == 4:
                        if tile[1] == 0:
                            esctiles.add(Diamond(levelx, levely))
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
                    if tile[0] == 14:
                        if len(tile) == 5:
                            guards.add(Guard(levelx, levely, tile[1], path=tile[2], facing=tile[3], speed=tile[4]))
                        elif len(tile) == 4:
                            guards.add(Guard(levelx, levely, tile[1], path=tile[2], facing=tile[3]))
                        elif len(tile) == 3:
                            guards.add(Guard(levelx, levely, tile[1], path=tile[2]))
                        else:
                            guards.add(Guard(levelx, levely, tile[1]))

                if not bgloaded:
                    spacetiles.add(Space(levelx, levely))

                levelx += 1 * size
            levelx = 0
            levely += 1 * size
        levely = 0

        if spawn is None:
            raise RuntimeError("No spawn found")

        spritesbg.add(spacetiles, lavatiles, circuittiles)
        sprites.add(blocktiles, spawn, rocktiles, turrettiles, lighttiles, pistonrodtiles, droppertiles, conveyortiles,
                    conductortiles)
        sprites2.add(esctiles, elevtiles, switchtiles, doortiles, pistontiles)
        projectiles.add(bullets)
        solidtiles.add(blocktiles, elevtiles, doortiles, rocktiles, turrettiles, lighttiles, pistontiles,
                       pistonrodtiles, droppertiles, conveyortiles, conductortiles, bullets)
        collidetiles.add(solidtiles, glasstiles)
        tiles.add(spritesbg, sprites, sprites2)
        fallingtiles.add([s for s in tiles if s.weight < 1])
        Elev.collidetiles.add([s for s in tiles if s not in circuittiles and s not in fallingtiles])

        if lighttiles or guards:
            stealth = True
            Esc(-32, -32).add(esctiles, tiles, sprites)
            shadowsurf.fill(colors.DGRAY)
            Light.polycache = shca.tiletopoly([s for s in solidtiles if s not in lighttiles])
            lighttiles.update()
            lightingtiles.update()

        plat.die("respawn", "game")

    # if stealth:
    #     Light.polycache = shca.tiletopoly([s for s in solidtiles if s not in lighttiles])
    if lavadeath := pygame.sprite.spritecollide(plat, lavatiles, False):
        plat.die("lava", lavadeath)
    if escapes := pygame.sprite.spritecollide(plat, esctiles, False):
        fakeescapes = [s for s in escapes if s.__class__ != Esc]
        if len(fakeescapes) == len(escapes):
            for escape in fakeescapes:
                if isinstance(escape, Diamond):
                    escape.rect.x, escape.rect.y = -32, -32
                    for tile in esctiles:
                        if tile.__class__ == Esc and tile.rect.topleft == (-32, -32):
                            tile.rect.x, tile.rect.y = spawn.rect.x, spawn.rect.y

        else:
            animations['cutscene'] = False
            invisiblespawn = False
            if levelcount == 4 - 1:
                animations['cutscene'] = True
                invisiblespawn = True
                zoom = 12
                plat.momentum = 0
                plat.vertforce = 0
                animations['animlive'] = True
            plat.escaped = True
    power.conductorcache = [s for s in conductortiles if s.on]
    if animations['cutscene']:
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
    fallingtiles.update()
    conductortiles.update()
    elevtiles.update()
    switchtiles.update()
    turrettiles.update()
    pistontiles.update()
    projectiles.update()
    guards.update()
    plat.move()

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
