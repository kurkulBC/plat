import pygame
import pygame.font as fonts
from assets.data.lvldata import levels as levels
from assets.data.lvldata import leveldescs as leveldescs
from assets.data.lvldata import anims as anims
import assets.data.colors as colors
import assets.hax as hax
from assets.data.common import screenwidth, screenheight, width, height, size, Direction, ShakeLayered, boundscheck
import random
from glitch_this import ImageGlitcher
import timeit
from assets.data import shadowcasting as shca
from assets.data import tilegroups
from math import dist, copysign

# pygame.init() - init ~1.7s
# this - init ~0.1s :)
try:
    pygame.mixer.init()
except pygame.error:
    pass
pygame.font.init()

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
droppertiles = pygame.sprite.Group()
droplets = pygame.sprite.Group()
conveyortiles = pygame.sprite.Group()
conductortiles = pygame.sprite.Group()
grapplertiles = pygame.sprite.Group()
hooktiles = pygame.sprite.Group()
hooktrails = pygame.sprite.Group()
sensortiles = pygame.sprite.Group()
shiftertiles = pygame.sprite.Group()

# create special groups
projectiles = pygame.sprite.Group()
solidtiles = pygame.sprite.Group()
collidetiles = pygame.sprite.Group()
fallingtiles = pygame.sprite.Group()
bgtiles = pygame.sprite.Group()
tiles = ShakeLayered()

guards = pygame.sprite.Group()
wireless = pygame.sprite.Group()

# load sound
ost = pygame.mixer.music
sfx = {
    # like this so it doesn't return an error
    s: pygame.mixer.Sound(f"assets/sfx/crush.ogg") for s in
    [
        'crush',
        'melt',
        'shoot',
        'hit',
        'shotkill',
        'press',
        'break',
        'drop',

        'hook',
        'reel',
        'pick',
    ]
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
    levelcount = 5 - 2
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
        self.transportmomentum = [0, 0]
        self.moving = False
        self.alive = True
        self.vertforce = 0
        self.gravity = 1.25
        self.jumpheight = 18
        self.tvel = 30
        self.jumping = False
        self.minjump = 1
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
        global framerate
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
            if keys[pygame.K_i]:
                framerate = 1

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

        blocked = False
        for tile1 in collidedtiles:
            if isinstance(tile1, Door):
                blocked = True

        for tile1 in collidedtiles:
            if self.transportmomentum[0] > 0 or self.momentum > 0:
                if self.weight >= tile1.weight and not blocked:
                    push(Direction.right, self)
                self.rect.right = tile1.rect.left
                self.momentum = 0
            elif self.transportmomentum[0] < 0 or self.momentum < 0:
                if self.weight >= tile1.weight and not blocked:
                    push(Direction.left, self)
                self.rect.left = tile1.rect.right
                self.momentum = 0

        self.rect.y -= self.vertforce
        collidedtiles = pygame.sprite.spritecollide(self, collidetiles, False)

        blocked = False
        for tile1 in collidedtiles:
            if isinstance(tile1, Door):
                blocked = True

        for tile1 in collidedtiles:
            if self.transportmomentum[1] < 0 or self.vertforce < 0:
                if self.weight >= tile1.weight and not blocked:
                    push(Direction.down, self)
                self.rect.bottom = tile1.rect.top
                self.vertforce = 0
            elif self.transportmomentum[1] > 0 or self.vertforce > 0:
                if self.weight >= tile1.weight and not blocked:
                    push(Direction.up, self)
                self.rect.top = tile1.rect.bottom
                self.vertforce = 0

        if self.rect.top < 0:
            self.rect.top = 0
            self.vertforce = 0
        if self.rect.left < 0:
            self.rect.left = 0
            self.momentum = 0
        if self.rect.bottom > height:
            self.rect.bottom = height
            self.vertforce = 0
        if self.rect.right > width:
            self.rect.right = width
            self.momentum = 0

        self.transportmomentum = [0, 0]
        if collidedtiles := pygame.sprite.spritecollide(self, collidetiles, False):
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
            wireless.update()
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
            pos = [win.get_width(), win.get_height()]
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
def power(sprite: pygame.sprite.Sprite, aslist=True, exact=False) -> dict[Direction, pygame.sprite.Sprite]:
    """
    :param sprite: the sprite to power
    :param aslist: returns power as a dict if turned on, else bool
    :param exact: only counts being powered from a direction if the
    power source is exactly aligned
    :return: dict of (direction -> sprite powered from direction?),
    or, if aslist is False, bool of if the sprite has any power
    """
    powered = {
        Direction.up: None,
        Direction.left: None,
        Direction.down: None,
        Direction.right: None,
    }
    doors = [s for s in doortiles if s.on]

    sprite.rect.y -= 1
    uppower = pygame.sprite.spritecollideany(sprite, [*rocktiles, *power.conductorcache])
    upblock = pygame.sprite.spritecollideany(sprite, doors)
    sprite.rect.y += 1
    while uppower and not upblock:
        if exact and uppower.rect.x != sprite.rect.x:
            break
        if not aslist:
            return uppower
        powered[Direction.up] = uppower
        break

    sprite.rect.x -= 1
    leftpower = pygame.sprite.spritecollideany(sprite, [*rocktiles, *power.conductorcache])
    leftblock = pygame.sprite.spritecollideany(sprite, doors)
    sprite.rect.x += 1
    while leftpower and not leftblock:
        if exact and leftpower.rect.y != sprite.rect.y:
            break
        if not aslist:
            return leftpower
        powered[Direction.left] = leftpower
        break

    sprite.rect.y += 1
    downpower = pygame.sprite.spritecollideany(sprite, [*rocktiles, *power.conductorcache])
    downblock = pygame.sprite.spritecollideany(sprite, doors)
    sprite.rect.y -= 1
    while downpower and not downblock:
        if exact and downpower.rect.x != sprite.rect.x:
            break
        if not aslist:
            return downpower
        powered[Direction.down] = downpower
        break

    sprite.rect.x += 1
    rightpower = pygame.sprite.spritecollideany(sprite, [*rocktiles, *power.conductorcache])
    rightblock = pygame.sprite.spritecollideany(sprite, doors)
    sprite.rect.x -= 1
    while rightpower and not rightblock:
        if exact and rightpower.rect.y != sprite.rect.y:
            break
        if not aslist:
            return rightpower
        powered[Direction.right] = rightpower
        break

    return powered if aslist else False


power.conductorcache = pygame.sprite.Group()


# image glitching
def glitch(image):
    """
    :param image: image to apply a glitch effect to
    :return: the image after the glitch effect is applied
    """
    global glitchimg
    random.seed(random.randint(1, 20000000))
    x = random.random()
    glitchimg = glitcher.glitch_image(src_img=image, glitch_amount=5, seed=x, color_offset=True, frames=1)
    glitchimg.save(r"assets\img\anims\glitchimg.png", format="PNG")
    return glitchimg


# anim system
def animate():
    """
    :return: nothing
    """
    global animations
    global shadowsurf
    global zoom
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
                vortextiles.update("assets/imgx/escape.png")
                vortextiles.update("assets/imgx/spawn.png", 1)
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
        plat.airaccel = 0.3
        plat.deaccel = 4
        plat.airdeaccel = 0.5
        plat.acceleration = 0
        plat.vel = 10
        plat.turnrate = 8
        plat.transportmomentum = [0, 0]
        plat.moving = False
        plat.alive = True
        plat.vertforce = 0
        plat.gravity = 1.25
        plat.jumpheight = 12
        plat.tvel = 30
        plat.jumping = False
        plat.minjump = 1
        plat.maxjump = plat.jumpheight / plat.gravity
        plat.jumpholding = False
        plat.jumptime = 0
        plat.jumpsmoothing = 5
        plat.jumprelease = 0
        plat.weight = 0
        plat.grounded = True
        plat.escaped = True


# screenshake
def shake(shakeduration=30, xshakeintensity=20, yshakeintensity=20, xshakedecay=1, yshakedecay=1):
    """
    :param shakeduration: how long the shake lasts
    :param xshakeintensity: how severe the shake is horizontally (in pixels)
    :param yshakeintensity: how severe the shake is vertically (in pixels)
    :param xshakedecay: how many pixels xshakeintensity decreases per frame
    :param yshakedecay: how many pixels yshakeintensity decreases per frame
    :return: nothing
    """
    global shaketime, shakeintensity, shakedecay

    shaketime = shakeduration
    shakeintensity = [xshakeintensity, yshakeintensity]
    shakedecay = [xshakedecay, yshakedecay]


# push things around
# entities won't push themselves, but safesprites won't be pushed by instigators
def push(direction: Direction, *instigators: pygame.sprite.Sprite, safesprites: list = None, weight=None, mercy=True):
    """
    :param direction: the direction to push
    :param instigators: the tiles that are pushing
    :param safesprites: the tiles that should not be pushed this call
    :param weight: how powerful the push force is, tiles with a higher weight won't be pushed
    :param mercy: if off, collisions with lower weight will effectively be killed
    :return: nothing
    """
    if direction not in Direction:
        raise ValueError("Direction required as input")
    if not isinstance(safesprites, list):
        safesprites = [safesprites]
    nextcollide = []
    for entity in instigators:
        collisiongroup = [s for s in solidtiles if s != entity and s not in safesprites]
        collided = pygame.sprite.spritecollide(entity, collisiongroup, False)
        for collision in collided:
            if not hasattr(collision, "weight") or \
                    collision.weight <= (weight if weight is not None else entity.weight):
                if direction == Direction.up:
                    collision.rect.bottom = entity.rect.top
                if direction == Direction.left:
                    collision.rect.right = entity.rect.left
                if direction == Direction.down:
                    collision.rect.top = entity.rect.bottom
                if direction == Direction.right:
                    collision.rect.left = entity.rect.right
                nextcollide.append(collision)
            else:
                if not mercy:
                    entity.rect.x, entity.rect.y = -32, -32
                    continue
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
        push(direction, *nextcollide)


# tile parent classes
class Tile(pygame.sprite.Sprite):
    def __init__(self, img, x=0, y=0, convert_alpha=False, rotate=0, weight=1, flip=False, layer=0):
        super().__init__()
        self.x = x
        self.y = y
        self.weight = weight  # <0 pushable, <1 falling
        self.shaded = False
        self.image = None
        self.mask = None
        if convert_alpha:
            self.image = pygame.image.load(f"assets/img/{img}.png").convert_alpha()
        else:
            self.image = pygame.image.load(f"assets/img/{img}.png").convert()
        self.image = pygame.transform.rotate(self.image, rotate * 90)
        self.mask = pygame.mask.from_surface(self.image)

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
        self._layer = layer

        self.vertforce = 0
        self.gravity = plat.gravity
        self.tvel = plat.tvel
        self.grounded = False
        self.transportmomentum = [0, 0]

    def update(self) -> bool:
        if not plat.alive:
            self.rect.x, self.rect.y = self.x, self.y
            return False

        if self.weight < 1 and self.alive():
            self.gravitycalc()

        return True

    def push(self, direction: Direction):
        pass

    def populategroups(self) -> pygame.sprite.Sprite:
        tiles.add(self)
        if hasattr(tilegroups, self.__class__.__name__):
            try:
                self.add(*[eval(s) for s in eval(f"tilegroups.{self.__class__.__name__}")])
            except RuntimeError:
                raise RuntimeError(f"populategroups() didn't work for {self.__class__.__name__}")
        else:
            raise NotImplementedError(f"Class '{self.__class__.__name__}' not defined in tilegroups.py")
        return self

    def coverededge(self, direction: Direction = None):
        # this way it can be (evaluated if direction is specified else iterated)
        if pygame.sprite.spritecollide(self, [s for s in solidtiles if s != self], False):
            return {
                'up': True,
                'left': True,
                'down': True,
                'right': True,
            }

        tempgroup = [s for s in solidtiles if s != self]
        if direction is None:
            coverededges = {}

            self.rect.y -= 1
            coverededges['up'] = any([pygame.sprite.spritecollideany(self, tempgroup), self.rect.top < 0])
            self.rect.y += 1

            self.rect.x -= 1
            coverededges['left'] = any([pygame.sprite.spritecollideany(self, tempgroup), self.rect.left < 0])
            self.rect.x += 1

            self.rect.y += 1
            coverededges['down'] = any([pygame.sprite.spritecollideany(self, tempgroup), self.rect.bottom > height])
            self.rect.y -= 1

            self.rect.x += 1
            coverededges['right'] = any([pygame.sprite.spritecollideany(self, tempgroup), self.rect.right > width])
            self.rect.x -= 1

            return coverededges

        else:
            covered = None

            if direction == Direction.up:
                self.rect.y -= 1
                covered = any([pygame.sprite.spritecollideany(self, tempgroup), self.rect.top < 0])
                self.rect.y += 1
            if direction == Direction.left:
                self.rect.x -= 1
                covered = any([pygame.sprite.spritecollideany(self, tempgroup), self.rect.left < 0])
                self.rect.x += 1
            if direction == Direction.down:
                self.rect.y += 1
                covered = any([pygame.sprite.spritecollideany(self, tempgroup), self.rect.bottom > height])
                self.rect.y -= 1
            if direction == Direction.right:
                self.rect.x += 1
                covered = any([pygame.sprite.spritecollideany(self, tempgroup), self.rect.right > width])
                self.rect.x -= 1

            if covered is not None:
                return covered

        raise ValueError("Direction required as input")

    def coveredcorner(self, coverededges=None):
        if coverededges is None:
            coverededges = [True, True, True, True]

        tempgroup = [s for s in tiles if s not in solidtiles and s != self]
        coveredcorners = {
            'upleft': False,
            'downleft': False,
            'downright': False,
            'upright': False,
        }

        if coverededges['up'] or coverededges['left']:
            self.rect.x -= 1
            self.rect.y -= 1
            coveredcorners['upleft'] = any([not pygame.sprite.spritecollideany(self, tempgroup),
                                            self.rect.top < 0, self.rect.left < 0])
            self.rect.x += 1
            self.rect.y += 1

        if coverededges['left'] or coverededges['down']:
            self.rect.x -= 1
            self.rect.y += 1
            coveredcorners['downleft'] = any([not pygame.sprite.spritecollideany(self, tempgroup),
                                              self.rect.bottom > height, self.rect.left < 0])
            self.rect.x += 1
            self.rect.y -= 1

        if coverededges['down'] or coverededges['right']:
            self.rect.x += 1
            self.rect.y += 1
            coveredcorners['downright'] = any([not pygame.sprite.spritecollideany(self, tempgroup),
                                               self.rect.bottom > height, self.rect.right > width])
            self.rect.x -= 1
            self.rect.y -= 1

        if coverededges['right'] or coverededges['up']:
            self.rect.x += 1
            self.rect.y -= 1
            coveredcorners['upright'] = any([not pygame.sprite.spritecollideany(self, tempgroup),
                                             self.rect.top < 0, self.rect.right > width])
            self.rect.x -= 1
            self.rect.y += 1

        return coveredcorners

    def shaded(self):
        if stealth and shadowsurf.get_at(self.rect.center) != (0, 0, 0, 255):
            return True
        return False

    def gravitycalc(self):
        if self.weight >= 1:
            return
        if pygame.sprite.spritecollideany(self, [s for s in doortiles if s.on]):
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
            if self.transportmomentum[1] < 0 or self.vertforce < 0:
                self.rect.bottom = tile1.rect.top
                self.vertforce = 0
            elif self.transportmomentum[1] > 0 or self.vertforce > 0:
                self.rect.top = tile1.rect.bottom
                self.vertforce = 0
            elif self.transportmomentum[0] < 0:
                self.rect.left = tile1.rect.right
            elif self.transportmomentum[0] > 0:
                self.rect.right = tile1.rect.left
        if self.rect.bottom > height:
            self.rect.bottom = height
            self.vertforce = 0
        if self.rect.top < 0:
            self.rect.top = 0
            self.vertforce = 0

        self.transportmomentum = [0, 0]
        collidedtiles = pygame.sprite.spritecollide(self, [s for s in collidetiles if s != self], False)
        if collidedtiles:
            if not hax.active or not hax.noclip:
                if not mute:
                    sfx['crush'].play()
                self.rect.x, self.rect.y = -32, -32
        if pygame.sprite.spritecollideany(self, lavatiles):
            if not mute:
                sfx['melt'].play()
            self.rect.x, self.rect.y = -32, -32


class TempObj(pygame.sprite.Sprite):
    def __init__(self, img=None, x=0, y=0, convert_alpha=False, rotate=0, weight=-1, layer=0):
        super().__init__()
        if img is not None:
            if convert_alpha:
                self.image = pygame.image.load(f"assets/img/{img}.png").convert_alpha()
                self.mask = pygame.mask.from_surface(self.image)
            else:
                self.image = pygame.image.load(f"assets/img/{img}.png").convert()
            self.image = pygame.transform.rotate(self.image, rotate)
            self.rect = self.image.get_rect()
            self.rect.x, self.rect.y = x, y
        self.weight = weight
        self._layer = layer

    def update(self) -> bool:
        if not plat.alive:
            self.kill()
            return False
        return True

    def populategroups(self) -> pygame.sprite.Sprite:
        tiles.add(self)
        projectiles.add(self)
        if hasattr(tilegroups, self.__class__.__name__):
            try:
                self.add(*[eval(s) for s in eval(f"tilegroups.{self.__class__.__name__}") if s in globals()])
            except RuntimeError:
                pass
        else:
            raise NotImplementedError(f"Class '{self.__class__.__name__}' not defined in tilegroups.py")
        return self

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
        super().__init__('space', x, y, layer=-1)


class Block(Tile):
    def __init__(self, x, y):
        super().__init__('block', x, y)


class Spawn(Tile):
    def __init__(self, x, y):
        super().__init__("spawn", x, y)
        if invisiblespawn:
            self.image = pygame.image.load("assets/img/space.png").convert()
            self.rect = self.image.get_rect()


class Lava(Tile):
    def __init__(self, x, y):
        super().__init__("lava", x, y)


class Esc(Tile):
    def __init__(self, x, y):
        super().__init__("escape", x, y, layer=1)


class Elev(Tile):
    collidetiles = pygame.sprite.Group()
    follow = pygame.sprite.Group()

    def __init__(self, x, y, speed=2, img="elevator"):
        super().__init__(img, x, y, layer=1)
        self.direction = Direction.up
        self.speed = speed
        self.followers = []

    def update(self):
        if not super().update():
            self.direction = Direction.up
            return

        if power(self, False):
            return f"{self} powered"
        if pygame.sprite.spritecollideany(self, [s for s in doortiles if s.on]):
            return

        cls = type(self)

        canmove = {
            Direction.up: False,
            Direction.left: False,
            Direction.down: False,
            Direction.right: False,
        }
        touchtiles = {
            Direction.up: None,
            Direction.left: None,
            Direction.down: None,
            Direction.right: None,
        }
        localcollidetiles = [s for s in cls.collidetiles if s != self]

        self.rect.y -= self.speed
        touchtiles[Direction.up] = pygame.sprite.spritecollideany(self, localcollidetiles)
        if pygame.sprite.spritecollide(self, circuittiles, False) and not touchtiles[Direction.up]:
            canmove[Direction.up] = True
        self.rect.y += self.speed

        self.rect.x -= self.speed
        touchtiles[Direction.left] = pygame.sprite.spritecollideany(self, localcollidetiles)
        if pygame.sprite.spritecollide(self, circuittiles, False) and not touchtiles[Direction.left]:
            canmove[Direction.left] = True
        self.rect.x += self.speed

        self.rect.y += self.speed
        touchtiles[Direction.down] = pygame.sprite.spritecollideany(self, localcollidetiles)
        if pygame.sprite.spritecollide(self, circuittiles, False) and not touchtiles[Direction.down]:
            canmove[Direction.down] = True
        self.rect.y -= self.speed

        self.rect.x += self.speed
        touchtiles[Direction.right] = pygame.sprite.spritecollideany(self, localcollidetiles)
        if pygame.sprite.spritecollide(self, circuittiles, False) and not touchtiles[Direction.right]:
            canmove[Direction.right] = True
        self.rect.x -= self.speed

        change = 0

        # jumping right next to an elevator makes you fly (feature?)
        # but only when you jump on the left side while the elevator moves left
        # keeping bc funy
        if self.direction == Direction.up:
            if self.rect.top - self.speed < 0:
                change = self.rect.top
                self.rect.top = 0
                self.direction = Direction.left
            else:
                if canmove[self.direction]:
                    change = self.speed
                    self.rect.y -= self.speed
                elif touchtiles[self.direction] and (diff := touchtiles[self.direction].rect.bottom - self.rect.top):
                    change = diff
                    self.rect.top = touchtiles[self.direction].rect.bottom
                    self.direction = Direction.left
                else:
                    self.direction = Direction.left

            self.followers.extend(pygame.sprite.spritecollide(self, [plat, *cls.follow], False))
            for follower in self.followers:
                follower.transportmomentum[1] += change
                follower.rect.y -= change
                push(Direction.up, follower, mercy=False)

        elif self.direction == Direction.left:
            if self.rect.left - self.speed < 0:
                change = self.rect.left
                self.rect.left = 0
                self.direction = Direction.down
            else:
                if canmove[self.direction]:
                    change = self.speed
                    self.rect.x -= self.speed
                elif touchtiles[self.direction] and (diff := touchtiles[self.direction].rect.right != self.rect.left):
                    change = diff
                    self.rect.left = touchtiles[self.direction].rect.right
                    self.direction = Direction.down
                else:
                    self.direction = Direction.down

            self.followers.extend(pygame.sprite.spritecollide(self, [plat, *cls.follow], False))
            for follower in self.followers:
                follower.rect.x -= change
                follower.transportmomentum[0] -= change
                push(Direction.left, follower, mercy=False)

        elif self.direction == Direction.down:
            if self.rect.bottom + self.speed > height:
                change = height - self.rect.bottom
                self.rect.bottom = height
                self.direction = Direction.right
            else:
                if canmove[self.direction]:
                    change = self.speed
                    self.rect.y += self.speed
                elif touchtiles[self.direction] and (diff := touchtiles[self.direction].rect.top != self.rect.bottom):
                    change = diff
                    self.rect.bottom = touchtiles[self.direction].rect.top
                    self.direction = Direction.right
                else:
                    self.direction = Direction.right

            # lastcollide stops the player from seemingly hopping after running off an elevator
            # the reason behind hopping is that the elevator moves down, but the player doesn't get
            # pulled down because he has ceased contact with the elevator
            # nvm i removed it a while ago and forgot :P
            if self.direction != Direction.down:
                return
            self.rect.y -= self.speed + 1
            self.followers.extend(pygame.sprite.spritecollide(self, [plat, *cls.follow], False))
            self.rect.y += self.speed + 1
            followers2 = pygame.sprite.spritecollide(self, [plat, *cls.follow], False)
            for follower in self.followers:
                collision = False
                if follower.grounded:
                    if follower.rect.left < self.rect.left:
                        self.rect.x -= 2
                        collidedtiles = pygame.sprite.spritecollide(self, localcollidetiles, False)
                        self.rect.x += 2
                        for tile1 in collidedtiles:
                            if tile1.rect.top <= self.rect.top:
                                collision = True
                                break
                    if follower.rect.right > self.rect.right:
                        self.rect.x += 2
                        collidedtiles = pygame.sprite.spritecollide(self, localcollidetiles, False)
                        self.rect.x -= 2
                        for tile1 in collidedtiles:
                            if tile1.rect.top <= self.rect.top:
                                collision = True
                                break
                    if collision:
                        break
                follower.rect.y += change
                follower.transportmomentum[1] -= change
                push(Direction.down, follower, mercy=False)
                follower.vertforce -= self.speed
            for follower in followers2:
                follower.rect.top = self.rect.bottom

        elif self.direction == Direction.right:
            if self.rect.right + self.speed > width:
                change = width - self.rect.right
                self.rect.right = width
                self.direction = Direction.up
            else:
                if canmove[self.direction]:
                    change = self.speed
                    self.rect.x += self.speed
                elif touchtiles[self.direction] and (diff := touchtiles[self.direction].rect.left != self.rect.right):
                    change = diff
                    self.rect.right = touchtiles[self.direction].rect.left
                    self.direction = Direction.up
                else:
                    self.direction = Direction.up

            self.followers.extend(pygame.sprite.spritecollide(self, [plat, *cls.follow], False))
            for follower in self.followers:
                follower.rect.x += change
                follower.transportmomentum[0] += change
                push(Direction.right, follower, mercy=False)

        self.followers.clear()


class Circuit(Tile):
    def __init__(self, x, y):
        super().__init__("circuit", x, y, layer=-1)


class Switch(Tile):
    def __init__(self, x, y, ident):
        super().__init__("switch", x, y, True, layer=1)
        self.ident = ident
        self.pressed = False
        self.imgcache = {
            False: self.image,
            True: pygame.image.load("assets/img/switch2.png").convert_alpha(),
        }
        self.maskcache = {
            False: self.mask,
            True: pygame.mask.from_surface(self.imgcache[True]),
        }

    def update(self):
        if not super().update():
            return

        if pygame.sprite.spritecollideany(self, [plat, *fallingtiles], pygame.sprite.collide_mask):
            if not self.pressed:
                self.pressed = True
                self.image = self.imgcache[self.pressed]
                self.mask = self.maskcache[self.pressed]
                sfx['press'].play()
                print(f"Signal: ID {self.ident}")
                wireless.update(self.ident)

        else:
            # if you are still within the rect of the switch it won't be toggleable (to prevent accidental toggles)
            if not pygame.sprite.spritecollideany(self, [plat, *fallingtiles]):
                self.pressed = False
                self.image = self.imgcache[self.pressed]
                self.mask = self.maskcache[self.pressed]


class Door(Tile):
    def __init__(self, x, y, ident, startoff=False):
        super().__init__("door", x, y, True, weight=2, layer=1)
        self.ident = ident
        self.startoff = startoff
        self.on = not startoff

    def update(self, ident=-1):
        if not super().update():
            if self.startoff:
                self.kill()
                self.add(doortiles, wireless)
            else:
                self.populategroups()
            self.on = not self.startoff
            return

        if self.ident == ident:
            if self.on:
                self.kill()
                self.add(doortiles, wireless)
            else:
                self.populategroups()
            self.on = not self.on


class Rock(Tile):
    def __init__(self, x, y, weight=1):
        super().__init__("hotrock", x, y, weight=weight)


class Turret(Tile):
    def __init__(self, x, y, firerate=60, delay=0):
        super().__init__("turret", x, y)
        self.firerate = firerate
        self.delay = delay
        self.delaystorage = delay
        self.cooldown = 0

    def update(self):
        if not super().update():
            self.delay = self.delaystorage
            self.cooldown = 0
            return

        if self.delay > 0:
            self.delay -= 1
        else:
            if self.cooldown > 0:
                self.cooldown -= 1

            if self.cooldown <= 0:

                powered = power(self)

                if powered[Direction.up]:
                    Bullet(self.rect.midbottom[0] - size / 8, self.rect.midbottom[1],
                           Direction.down).populategroups()
                if powered[Direction.left]:
                    Bullet(self.rect.midright[0], self.rect.midright[1] - size / 8,
                           Direction.right).populategroups()
                if powered[Direction.down]:
                    Bullet(self.rect.midtop[0] - size / 8, self.rect.midtop[1] - size / 4,
                           Direction.up).populategroups()
                if powered[Direction.right]:
                    Bullet(self.rect.midleft[0] - size / 4, self.rect.midleft[1] - size / 8,
                           Direction.left).populategroups()
                self.cooldown = self.firerate
                if not mute:
                    sfx['shoot'].play()


class Bullet(TempObj):
    def __init__(self, x, y, direction, speed=5):
        super().__init__("bullet", x, y)
        self.rect.x, self.rect.y = x, y
        self.direction = direction
        self.speed = speed
        self.set = False

    def update(self):
        if not super().update():
            return

        if not self.set:
            self.populategroups()
            self.set = True

        if self.direction == Direction.up:
            self.rect.y -= self.speed
        elif self.direction == Direction.left:
            self.rect.x -= self.speed
        elif self.direction == Direction.down:
            self.rect.y += self.speed
        elif self.direction == Direction.right:
            self.rect.x += self.speed

        collide = pygame.sprite.spritecollideany(self, [s for s in solidtiles if s != self])
        charcollide = pygame.sprite.collide_rect(self, plat)
        if collide or not boundscheck(self.rect):
            self.kill()
            if not mute:
                sfx['hit'].play()
        if charcollide:
            plat.die("shot", self)
            self.kill()


class Light(Tile):
    polycache: list[list[shca.Coord], list[shca.Line]]

    def __init__(self, x, y):
        super().__init__("stealth/light", x, y)
        self.lighting: list[Lighting, Lighting, Lighting, Lighting] = [None, None, None, None]

    def push(self, direction: Direction):
        for lighting in self.lighting:
            lighting.kill()
        self.lighting = [None, None, None, None]

    def update(self):
        if not super().update():
            return

        powered = power(self)

        if powered[Direction.up]:
            self.lighting[0] = Lighting(self.rect.centerx, self.rect.centery, self.rect, Direction.down)
            lightingtiles.add(self.lighting[0])
        elif self.lighting[0]:
            self.lighting[0].kill()
            self.lighting[0] = None

        if powered[Direction.left]:
            self.lighting[1] = Lighting(self.rect.centerx, self.rect.centery, self.rect, Direction.right)
            lightingtiles.add(self.lighting[1])
        elif self.lighting[1]:
            self.lighting[1].kill()
            self.lighting[1] = None

        if powered[Direction.down]:
            self.lighting[2] = Lighting(self.rect.centerx, self.rect.centery, self.rect, Direction.up)
            lightingtiles.add(self.lighting[2])
        elif self.lighting[2]:
            self.lighting[2].kill()
            self.lighting[2] = None

        if powered[Direction.right]:
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
        if ident == self.ident:
            glitch(self.rawimg)
            self.rawimg = glitchimg
            if image == "":
                self.image = pygame.image.load("anims/glitchimg").convert()
            else:
                self.image = pygame.image.load(image).convert()


class Piston(Tile):
    def __init__(self, x, y, rotation=0, exact=False):
        super().__init__("piston", x, y, convert_alpha=True, rotate=rotation, layer=1)
        self.rotation = rotation
        self.child = None
        self.exact = exact

    def update(self):
        if not super().update():
            if self.child is not None:
                self.child.kill()
                self.child = None
            return

        if self.child is None or not self.child.groups():
            self.child = PistonRod(self.rect.x, self.rect.y, self, self.rotation, exact=self.exact)
            self.child.populategroups()

        self.child.update(power(self, False, self.exact))


class PistonRod(Tile):
    def __init__(self, x, y, host, rotation=0, speed=2, exact=False):
        super().__init__("pistonrod", x, y, convert_alpha=True, rotate=rotation)
        self.host = host
        self.rotation = rotation
        self.distance = 0
        self.speed = speed
        self.exact = exact

    def update(self, active=False):
        if not super().update():
            return

        if not active and power(self, False, self.exact):
            active = True
        if self.rotation % 2 == 0:
            self.rect.x = self.host.rect.x
        else:
            self.rect.y = self.host.rect.y

        if pygame.sprite.spritecollideany(self, [s for s in solidtiles if s != self and s != self.host]):
            self.kill()
            sfx['break'].play()

        if active:
            self.distance = min(self.distance + self.speed, 32)
        else:
            self.distance = max(0, self.distance - self.speed)

        if self.direction == Direction.up:
            self.rect.y = self.host.rect.y - self.distance
        elif self.direction == Direction.left:
            self.rect.x = self.host.rect.x - self.distance
        elif self.direction == Direction.down:
            self.rect.y = self.host.rect.y + self.distance
        elif self.direction == Direction.right:
            self.rect.x = self.host.rect.x + self.distance

        push(self.direction, self, safesprites=self.host)

    def push(self, direction: Direction):
        if direction == Direction.opposite(self.direction):
            if self.rotation % 2 == 0:
                self.distance = abs(self.rect.y - self.host.rect.y)
            else:
                self.distance = abs(self.rect.x - self.host.rect.x)


class Diamond(Tile):
    def __init__(self, x, y):
        super().__init__("stealth/diamond", x, y, True, layer=1)


class Glass(Tile):
    def __init__(self, x, y):
        super().__init__("stealth/glass", x, y, convert_alpha=True)

    def coverededge(self, direction: Direction = None):
        return {
            'up': True,
            'left': True,
            'down': True,
            'right': True,
        }

    def coveredcorner(self, coverededges=None):
        return {
            'upleft': True,
            'downleft': True,
            'downright': True,
            'upright': True,
        }


class Dropper(Tile):
    def __init__(self, x, y, ident, rotation=0):
        super().__init__("dropper", x, y, rotate=rotation)
        self.ident = ident
        self.child = None
        if self.direction == Direction.up:
            self.child = Droplet(self.rect.midtop[0] - size / 8, self.rect.midtop[1] - size / 4)
        elif self.direction == Direction.left:
            self.child = Droplet(self.rect.midleft[0] - size / 4, self.rect.midleft[1] - size / 8)
        elif self.direction == Direction.down:
            self.child = Droplet(self.rect.midbottom[0] - size / 8, self.rect.midbottom[1])
        elif self.direction == Direction.right:
            self.child = Droplet(self.rect.midright[0], self.rect.midright[1] - size / 8)

    def update(self, ident=-1):
        if not super().update():
            self.child.kill()
            return

        if not self.child.alive():
            if self.ident == ident or power(self, False):
                if self.direction == Direction.up:
                    self.child = Droplet(self.rect.midtop[0] - size / 8, self.rect.midtop[1] - size / 4)
                elif self.direction == Direction.left:
                    self.child = Droplet(self.rect.midleft[0] - size / 4, self.rect.midleft[1] - size / 8)
                elif self.direction == Direction.down:
                    self.child = Droplet(self.rect.midbottom[0] - size / 8, self.rect.midbottom[1])
                elif self.direction == Direction.right:
                    self.child = Droplet(self.rect.midright[0], self.rect.midright[1] - size / 8)
                self.child.populategroups()
                sfx['drop'].play()


class Droplet(Tile):
    def __init__(self, x, y):
        super().__init__("droplet", x, y, weight=-1)


class Conveyor(Tile):
    def __init__(self, x, y, facing=Direction.left, speed=2):
        super().__init__("conveyor", x, y, flip=facing not in (Direction.left, 'l'))
        self.facing = facing
        if isinstance(facing, str):
            if facing.lower() == 'l':
                self.facing = Direction.left
            elif facing.lower() == 'r':
                self.facing = Direction.right
            else:
                raise TypeError("facing must be a Direction, 'l', or 'r'")
        self.speed = -speed if facing == Direction.left else speed

    def update(self):
        if not super().update():
            return
        if not power(self, False):
            return

        self.rect.y -= 2
        collisions = pygame.sprite.spritecollide(self, [plat, *fallingtiles], False)
        self.rect.y += 2

        for collision in collisions:
            collision.rect.x += self.speed
            if collision is plat:
                collision.transportmomentum[0] += self.speed


class Conductor(Tile):
    def __init__(self, x, y):
        super().__init__("conductor", x, y, weight=-1)
        self.on = False
        self.imgcache = {
            False: self.image,
            True: pygame.image.load("assets/img/conductor2.png").convert(),
        }
        self.powersrc = None

    def update(self) -> bool:
        if not super().update():
            return

        on = power(self, False)
        if self.on is not bool(on):
            if not self.on:
                self.powersrc = on
            else:
                power.conductorcache.remove(self)
            self.on = not self.on
            self.image = self.imgcache[self.on]
        elif self.on and on is not self.powersrc and not isinstance(on, Rock):
            self.on = False
            self.image = self.imgcache[self.on]
            power.conductorcache.remove(self)


class Grappler(Tile):
    def __init__(self, x, y, ident, rotation=0, speed=10):
        super().__init__("grappler", x, y, rotate=rotation, layer=1)
        self.ident = ident
        self.rotation = rotation
        self.child = None
        self.on = True
        self.speed = -speed if rotation < 2 else speed
        self.trailcount = 0
        self.channel = None

    def update(self, ident=-1, connected=False):
        if not super().update():
            if self.child is not None:
                self.child = None
                self.on = True
                self.trailcount = 0
                self.channel = None
            return

        if connected:
            if self.rotation % 2 == 0:
                self.rect.y += self.speed
            else:
                self.rect.x += self.speed
            self.trailcount += self.speed

            if abs(self.trailcount) >= 32:
                self.trailcount -= size * copysign(1, self.trailcount)
                if self.rotation % 2 == 0:
                    for trail in self.child.trails:
                        if trail.rect.y == self.rect.y - self.trailcount:
                            trail.kill()
                            break
                else:
                    for trail in self.child.trails:
                        if trail.rect.x == self.rect.x - self.trailcount:
                            trail.kill()
                            break

            if self.channel is None:
                self.channel = sfx['reel'].play(-1)

            if pygame.sprite.collide_rect(self, self.child):
                self.rect.x, self.rect.y = self.child.rect.x, self.child.rect.y
                self.child.kill()
                self.child = None
                self.channel.stop()
                self.channel = None
            return

        if self.child and not self.child.alive():
            self.child = None

        if not self.child and ident == self.ident:
            tempgroup = [s for s in solidtiles if s != self]
            if self.rotation % 2 == 0:
                self.rect.y += self.speed
                blocked = pygame.sprite.spritecollideany(self, tempgroup)
                self.rect.y -= self.speed
            else:
                self.rect.x += self.speed
                blocked = pygame.sprite.spritecollideany(self, tempgroup)
                self.rect.x -= self.speed

            if not blocked:
                if self.direction == Direction.up:
                    self.child = Hook(self.rect.midtop[0] - size / 2, self.rect.midtop[1] - size,
                                      self, self.rotation, self.speed)
                elif self.direction == Direction.left:
                    self.child = Hook(self.rect.midleft[0] - size, self.rect.midleft[1] - size / 2,
                                      self, self.rotation, self.speed)
                elif self.direction == Direction.down:
                    self.child = Hook(self.rect.midbottom[0] - size / 2, self.rect.midbottom[1],
                                      self, self.rotation, self.speed)
                elif self.direction == Direction.right:
                    self.child = Hook(self.rect.midright[0], self.rect.midright[1] - size / 2,
                                      self, self.rotation, self.speed)
                self.child.populategroups()
                sfx['hook'].play()

        if self.child:
            self.child.update()


class Hook(Tile):
    def __init__(self, x, y, host: Grappler, rotation=0, speed=10):
        super().__init__("hook", x, y, convert_alpha=True, rotate=rotation, layer=1)
        self.host = host
        self.rotation = rotation
        self.speed = speed
        self.trails = pygame.sprite.Group(HookTrail(self.x, self.y, self.rotation).populategroups())
        self.trailcount = 0
        self.connected = False

    def update(self):
        if not super().update():
            for trail in self.trails:
                trail.kill()
            self.kill()
            return

        if self.connected:
            self.host.update(connected=True)
            return

        if pygame.sprite.groupcollide(self.trails, [s for s in solidtiles if s != self and s != self.host],
                                      True, False):
            self.kill()
            return

        if self.host.rotation % 2 == 0:
            self.rect.y += self.speed
        else:
            self.rect.x += self.speed

        if hit := pygame.sprite.spritecollideany(self, [s for s in solidtiles if s != self and s != self.host]):
            self.connected = True
            if self.direction == Direction.up:
                self.rect.top = hit.rect.bottom
            elif self.direction == Direction.left:
                self.rect.left = hit.rect.right
            elif self.direction == Direction.down:
                self.rect.bottom = hit.rect.top
            elif self.direction == Direction.right:
                self.rect.right = hit.rect.left
            return
        else:
            self.trailcount += self.speed

        if abs(self.trailcount) >= size:
            self.trailcount -= size * copysign(1, self.trailcount)
            if self.rotation % 2 == 0:
                trail = HookTrail(self.rect.x, self.rect.y - self.trailcount, self.host.rotation)
            else:
                trail = HookTrail(self.rect.x - self.trailcount, self.rect.y, self.host.rotation)
            trail.populategroups()
            self.trails.add(trail)


class HookTrail(TempObj):
    def __init__(self, x, y, rotate=0):
        super().__init__("hooktrail", x, y, convert_alpha=True, rotate=rotate)


class StickyElev(Elev):
    collidetiles = pygame.sprite.Group()
    follow = pygame.sprite.Group()

    def __init__(self, x, y, speed=2):
        super().__init__(x, y, speed, img="stickyelevator")

    def update(self):
        if Direction is not Direction.up:
            self.rect.y -= 1
            self.followers.extend(
                pygame.sprite.spritecollide(self, [s for s in StickyElev.follow if s.rect.x == self.rect.x], False))
            self.rect.y += 1
        if Direction is not Direction.left:
            self.rect.x -= 1
            self.followers.extend(
                pygame.sprite.spritecollide(self, [s for s in StickyElev.follow if s.rect.y == self.rect.y], False))
            self.rect.x += 1
        if Direction is not Direction.down:
            self.rect.y += 1
            self.followers.extend(
                pygame.sprite.spritecollide(self, [s for s in StickyElev.follow if s.rect.x == self.rect.x], False))
            self.rect.y -= 1
        if Direction is not Direction.right:
            self.rect.x += 1
            self.followers.extend(
                pygame.sprite.spritecollide(self, [s for s in StickyElev.follow if s.rect.y == self.rect.y], False))
            self.rect.x -= 1
        super().update()


class Sensor(Tile):
    def __init__(self, img, x, y, ident=-1, convert_alpha=False, rotate=0, remote=True, layer=0):
        super().__init__(img, x, y, convert_alpha=convert_alpha, rotate=rotate, layer=layer)
        self.ident = ident
        self.remote = remote
        self.on = False

    def update(self, *args):
        if not super().update():
            return

        if self.sense(*args):
            if self.remote:
                wireless.update(self.ident)
            else:
                self.on = True
        else:
            self.on = False

    def sense(self, *args) -> bool:
        if isinstance(self, Sensor):
            return True
        return False


class Transformer(Sensor):
    def __init__(self, x, y, ident=-1):
        super().__init__("transformer", x, y, ident, remote=False)
        self.lastpower = False
        self.imgcache = {
            False: self.image,
            True: pygame.image.load("assets/img/transformer2.png").convert()
        }

    def sense(self, ident=-1) -> bool:
        if self.ident == ident:
            self.lastpower = not self.lastpower
            self.image = self.imgcache[self.lastpower]
        return self.lastpower


class Broadcaster(Sensor):
    def __init__(self, x, y, ident=-1):
        super().__init__("broadcaster", x, y, ident)
        self.lastpower = False
        self.imgcache = {
            False: self.image,
            True: pygame.image.load("assets/img/broadcaster2.png").convert()
        }

    def sense(self) -> bool:
        if bool(power(self, False)) is not self.lastpower:
            self.lastpower = not self.lastpower
            self.image = self.imgcache[self.lastpower]
            return True
        return False


class Picker(Sensor):
    def __init__(self, x, y, ident=-1, rotation=0):
        super().__init__("picker", x, y, ident, convert_alpha=True, rotate=rotation)

    def sense(self) -> bool:
        contact = None
        if self.direction == Direction.up:
            self.rect.y -= 1
            contact = pygame.sprite.spritecollideany(self, droplets)
            self.rect.y += 1
        elif self.direction == Direction.left:
            self.rect.x -= 1
            contact = pygame.sprite.spritecollideany(self, droplets)
            self.rect.x += 1
        elif self.direction == Direction.down:
            self.rect.y += 1
            contact = pygame.sprite.spritecollideany(self, droplets)
            self.rect.y -= 1
        elif self.direction == Direction.right:
            self.rect.x += 1
            contact = pygame.sprite.spritecollideany(self, droplets)
            self.rect.x -= 1

        if contact:
            contact.kill()
            sfx['pick'].play()
            return True
        return False


class Tripwire(Sensor):
    def __init__(self, x, y, ident=-1, rotation=0):
        super().__init__("tripwire", x, y, ident, rotate=rotation)
        self.rotation = rotation
        self.child = Wire(self)
        tiles.add(self.child)
        self.speed = -size if self.rotation < 2 else size
        self.prevhit = False
        self.imgcache = {
            False: self.image,
            True: pygame.transform.rotate(pygame.image.load("assets/img/tripwire2.png").convert(), rotation * 90),
        }

    def sense(self) -> bool:
        self.child.rect.x, self.child.rect.y = self.rect.x + 12, self.rect.y + 12
        self.child.rect.width, self.child.rect.height = 8, 8
        if not power(self, False):
            self.image = self.imgcache[False]
            self.child.update()
            return False
        self.image = self.imgcache[True]

        tempgroup = [s for s in (plat, *fallingtiles, *solidtiles) if s != self]
        while not (collision := pygame.sprite.spritecollideany(self.child, tempgroup)) and boundscheck(self.child.rect):
            if self.rotation % 2 == 0:
                self.child.rect.y += self.speed
            else:
                self.child.rect.x += self.speed

        if self.direction == Direction.up:
            if collision:
                self.child.rect.top = collision.rect.bottom
            self.child.rect.height = self.rect.y + 12 - self.child.rect.top
        elif self.direction == Direction.left:
            if collision:
                self.child.rect.left = collision.rect.right
            self.child.rect.width = self.rect.x + 12 - self.child.rect.left
        elif self.direction == Direction.down:
            if collision:
                self.child.rect.bottom = collision.rect.top
            self.child.rect.height = self.child.rect.bottom - self.rect.y + 12
            self.child.rect.y = self.rect.y + 12
        elif self.direction == Direction.right:
            if collision:
                self.child.rect.right = collision.rect.left
            self.child.rect.width = self.child.rect.right - self.rect.x + 12
            self.child.rect.x = self.rect.x + 12
        self.child.update()

        if collision in (plat, *fallingtiles):
            if not self.prevhit:
                self.prevhit = True
                return True
        else:
            self.prevhit = False
        return False


class Wire(TempObj):
    def __init__(self, host):
        super().__init__(weight=1, layer=1)
        self.rect = pygame.rect.Rect(host.x + 12, host.y + 12, 8, 8)
        self.image = pygame.Surface((self.rect.width, self.rect.height))
        self.image.fill(colors.RED)

    def update(self):
        if not plat.alive:
            return

        if self.image.get_rect() != self.rect:
            self.image = pygame.Surface((self.rect.width, self.rect.height))
            self.image.fill(colors.RED)


class Magma(Lava):
    def __init__(self, x, y, spreadspace=3, spreaddelay=30, spawned=False):
        super().__init__(x, y)
        self.spreadspace = spreadspace
        self.spreaddelay = spreaddelay
        self.spreadtime = self.spreaddelay
        self.spawned = spawned
        self.done = False

    def update(self):
        if not super().update():
            if self.spawned:
                self.kill()
            self.spreadtime = self.spreaddelay
            self.done = False
            return

        if self.done:
            return
        self.spreadtime -= 1 if self.spreadtime else 0
        if self.spreadtime != 0 or pygame.sprite.spritecollideany(self, solidtiles):
            return

        otherlava = [s for s in lavatiles if s != self]

        self.rect.y += size
        if not self.tryspawn():
            self.rect.y -= size

            self.rect.x -= size
            self.tryspawn()
            self.rect.x += size

            self.rect.x += size
            self.tryspawn()
            self.rect.x -= size

            self.rect.y += size
        self.rect.y -= size

        for i in range(self.spreadspace):
            self.rect.y -= size
            if not [s for s in pygame.sprite.spritecollide(self, otherlava, False)]:
                self.rect.y += size * (i + 1)
                break
        else:
            self.rect.y += size * self.spreadspace

            self.rect.x -= size
            self.tryspawn()
            self.rect.x += size

            self.rect.x += size
            self.tryspawn()
            self.rect.x -= size

        self.spreadtime = self.spreaddelay

        if self.spawned:
            self.rect.y -= size
            if [s for s in pygame.sprite.spritecollide(self, otherlava, False)]:
                self.rect.y += size
            else:
                self.rect.y += size
                self.rect.x -= size
                if [s for s in pygame.sprite.spritecollide(self, otherlava, False)]:
                    self.rect.x += size
                else:
                    self.rect.x += size
                    self.rect.x += size
                    if [s for s in pygame.sprite.spritecollide(self, otherlava, False)]:
                        self.rect.x -= size
                    else:
                        self.kill()

        self.done = True

    def tryspawn(self):
        if [s for s in pygame.sprite.spritecollide(self, bgtiles, False)] and \
                not pygame.sprite.spritecollideany(self, solidtiles) and boundscheck(self.rect):
            Magma(self.rect.x, self.rect.y, self.spreadspace, self.spreaddelay, True).populategroups()
            return True
        return False


class Shifter(Tile):
    def __init__(self, x, y, ident=-1):
        super().__init__("shifter", x, y)
        self.ident = ident


# refresh every frame
def redrawgamewindow():
    # ~10ms

    # tiles -> guards -> particles -> plat -> lighting
    tiles.draw(win, screenshake)
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
    if stealth:
        win.blit(shadowsurf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        for sprite in lightingtiles:
            for coord in sprite.visiblepolycache[0]:
                pygame.draw.circle(win, colors.RED, coord, 2)
        #     for coord in Light.polycache[0]:
        #         pygame.draw.line(win, colors.RED, sprite.rect.center, coord)
        # for coord in Light.polycache[0]:
        #     pygame.draw.circle(win, colors.RED, coord, 2)

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
# TODO: 8 - transformers/broadcasters/conductors, 9 - grapplers/sticky elevators,
#  10 - multi-level stages/boss
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
                if isinstance(tile, int):
                    if tile == 0:
                        spacetiles.add(Space(levelx, levely))
                        bgloaded = True
                    elif tile == 1:
                        blocktiles.add(Block(levelx, levely))
                    elif tile == 2:
                        spawn = Spawn(levelx, levely)
                    elif tile == 3:
                        lavatiles.add(Lava(levelx, levely))
                        bgloaded = True
                    elif tile == 4:
                        esctiles.add(Esc(levelx, levely))
                    elif tile == 5:
                        circuittiles.add(Circuit(levelx, levely))
                        bgloaded = True
                        elevtiles.add(Elev(levelx, levely))
                    elif tile == 6:
                        circuittiles.add(Circuit(levelx, levely))
                        bgloaded = True
                    elif tile == 9:
                        rocktiles.add(Rock(levelx, levely))
                    elif tile == 10:
                        turrettiles.add(Turret(levelx, levely))
                    elif tile == 11:
                        lighttiles.add(Light(levelx, levely))
                    elif tile == 14:
                        guards.add(Guard(levelx, levely))
                    elif tile == 16:
                        conveyortiles.add(Conveyor(levelx, levely))
                    elif tile == 17:
                        conductortiles.add(Conductor(levelx, levely))
                    elif tile == 19:
                        circuittiles.add(Circuit(levelx, levely))
                        bgloaded = True
                        elevtiles.add(StickyElev(levelx, levely))
                elif isinstance(tile, list):
                    if tile[0] == 1:
                        if tile[1] == 0:
                            blocktiles.add(Glass(levelx, levely))
                    elif tile[0] == 3:
                        if tile[1] == 0:
                            lavatiles.add(Magma(levelx, levely))
                            bgloaded = True
                    elif tile[0] == 4:
                        if tile[1] == 0:
                            esctiles.add(Diamond(levelx, levely))
                    elif tile[0] == 5:
                        circuittiles.add(Circuit(levelx, levely))
                        bgloaded = True
                        elevtiles.add(Elev(levelx, levely, tile[1]))
                    elif tile[0] == 7:
                        spacetiles.add(Space(levelx, levely))
                        bgloaded = True
                        switchtiles.add(Switch(levelx, levely, tile[1]))
                    elif tile[0] == 8:
                        if isinstance(tile[2], int):
                            if tile[2] == 0:
                                spacetiles.add(Space(levelx, levely))
                                bgloaded = True
                            elif tile[2] == 1:
                                blocktiles.add(Block(levelx, levely))
                            elif tile[2] == 3:
                                lavatiles.add(Lava(levelx, levely))
                                bgloaded = True
                            elif tile[2] == 4:
                                esctiles.add(Esc(levelx, levely))
                            elif tile[2] == 5:
                                circuittiles.add(Circuit(levelx, levely))
                                bgloaded = True
                                elevtiles.add(Elev(levelx, levely))
                            elif tile[2] == 6:
                                circuittiles.add(Circuit(levelx, levely))
                                bgloaded = True
                            elif tile[2] == 9:
                                rocktiles.add(Rock(levelx, levely))
                            elif tile[2] == 10:
                                if len(tile) == 5:
                                    turrettiles.add(Turret(levelx, levely, tile[3], tile[4]))
                                elif len(tile) == 4:
                                    turrettiles.add(Turret(levelx, levely, tile[3]))
                                else:
                                    turrettiles.add(Turret(levelx, levely))
                            elif tile[2] == 11:
                                lighttiles.add(Light(levelx, levely))
                        elif isinstance(tile[2], list):
                            if tile[2] == [3, 0]:
                                lavatiles.add(Magma(levelx, levely))
                                bgloaded = True

                        if len(tile) == 4:
                            doortiles.add(Door(levelx, levely, tile[1], tile[3]))
                        else:
                            doortiles.add(Door(levelx, levely, tile[1]))
                    elif tile[0] == 9:
                        rocktiles.add(Rock(levelx, levely, tile[1]))
                    elif tile[0] == 10:
                        if len(tile) == 3:
                            turrettiles.add(Turret(levelx, levely, tile[1], tile[2]))
                        elif len(tile) == 2:
                            turrettiles.add(Turret(levelx, levely, tile[1]))
                        else:
                            turrettiles.add(Turret(levelx, levely))
                    elif tile[0] == 12:
                        vortextiles.add(Vortex(levelx, levely, tile[1], "assets/imgx/anims/greenglitch.png",
                                               "escape"))
                        # if tile[1] == 0:
                        #     prevortextiles.append([levelx, levely, "assets/imgx/space.png"])
                        # if tile[1] == 1:
                        #     prevortextiles.append([levelx, levely, "assets/imgx/block.png"])
                        # if tile[1] == 2:
                        #     prevortextiles.append([levelx, levely, "assets/imgx/spawn.png"])
                        # if tile[1] == 3:
                        #     prevortextiles.append([levelx, levely, "assets/imgx/lava.png"])
                        # if tile[1] == 4:
                        #     prevortextiles.append([levelx, levely, "assets/imgx/escape.png"])
                        # if tile[1] == 5:
                        #     prevortextiles.append([levelx, levely, "assets/imgx/circuit.png"])
                        # if tile[1] == 6:
                        #     prevortextiles.append([levelx, levely, "assets/imgx/elevator.png"])
                    elif tile[0] == 13:
                        if len(tile) == 3:
                            pistontiles.add(Piston(levelx, levely, tile[1], tile[2]))
                        else:
                            pistontiles.add(Piston(levelx, levely, tile[1]))
                    elif tile[0] == 14:
                        if len(tile) == 5:
                            guards.add(Guard(levelx, levely, tile[1], path=tile[2], facing=tile[3], speed=tile[4]))
                        elif len(tile) == 4:
                            guards.add(Guard(levelx, levely, tile[1], path=tile[2], facing=tile[3]))
                        elif len(tile) == 3:
                            guards.add(Guard(levelx, levely, tile[1], path=tile[2]))
                        else:
                            guards.add(Guard(levelx, levely, tile[1]))
                    elif tile[0] == 15:
                        if len(tile) == 3:
                            droppertiles.add(Dropper(levelx, levely, tile[1], tile[2]))
                        else:
                            droppertiles.add(Dropper(levelx, levely, tile[1]))
                    elif tile[0] == 16:
                        if len(tile) == 3:
                            conveyortiles.add(Conveyor(levelx, levely, tile[1], tile[2]))
                        else:
                            conveyortiles.add(Conveyor(levelx, levely, tile[1]))
                    elif tile[0] == 18:
                        if len(tile) == 3:
                            grapplertiles.add(Grappler(levelx, levely, tile[1], tile[2]))
                        else:
                            grapplertiles.add(Grappler(levelx, levely, tile[1]))
                    elif tile[0] == 19:
                        circuittiles.add(Circuit(levelx, levely))
                        bgloaded = True
                        elevtiles.add(StickyElev(levelx, levely, tile[1]))
                    elif tile[0] == 20:
                        sensortiles.add(Transformer(levelx, levely, tile[1]))
                    elif tile[0] == 21:
                        sensortiles.add(Broadcaster(levelx, levely, tile[1]))
                    elif tile[0] == 22:
                        if len(tile) == 3:
                            sensortiles.add(Picker(levelx, levely, tile[1], tile[2]))
                        else:
                            sensortiles.add(Picker(levelx, levely, tile[1]))
                    elif tile[0] == 23:
                        if len(tile) == 3:
                            sensortiles.add(Tripwire(levelx, levely, tile[1], tile[2]))
                        else:
                            sensortiles.add(Tripwire(levelx, levely, tile[1]))

                if not bgloaded:
                    spacetiles.add(Space(levelx, levely))

                levelx += 1 * size
            levelx = 0
            levely += 1 * size
        levely = 0

        if spawn is None:
            raise RuntimeError("No spawn found")

        bgtiles.add(spacetiles, circuittiles)
        solidtiles.add(blocktiles, elevtiles, doortiles, rocktiles, turrettiles, lighttiles, pistontiles,
                       pistonrodtiles, droppertiles, conveyortiles, conductortiles, grapplertiles, sensortiles, bullets)
        collidetiles.add(solidtiles)
        wireless.add(doortiles, droppertiles, grapplertiles, [s for s in sensortiles if type(s) in (Transformer,)])

        tiles.add(spacetiles, blocktiles, spawn, lavatiles, esctiles, elevtiles, circuittiles, switchtiles, doortiles,
                  rocktiles, turrettiles, bullets, lighttiles, vortextiles, pistontiles, pistonrodtiles, droppertiles,
                  droplets, conveyortiles, conductortiles, grapplertiles, hooktiles, hooktrails, sensortiles)
        projectiles.add(bullets)

        fallingtiles.add([s for s in tiles if s.weight < 1])
        Elev.collidetiles.add([s for s in tiles if s not in circuittiles and s not in fallingtiles])
        Elev.follow.add([s for s in fallingtiles])
        StickyElev.collidetiles.add([s for s in Elev.collidetiles if s not in solidtiles])
        StickyElev.follow.add([s for s in fallingtiles] + [s for s in solidtiles if s not in elevtiles and
                                                           s.weight <= 1])

        if lighttiles or guards:
            stealth = True
            Esc(-32, -32).populategroups()
            shadowsurf.fill(colors.DGRAY)
            Light.polycache = shca.tiletopoly([s for s in solidtiles if s not in lighttiles])
            Light.polycache[0].update([(x * 32, y * 32) for x in range(33) for y in range(33)
                                       if x in (0, 32) or y in (0, 32)])
            lighttiles.update()
            lightingtiles.update()

        plat.die("respawn", "game")

    # if stealth:
    #     Light.polycache = shca.tiletopoly([s for s in solidtiles if s not in lighttiles])
    #     Light.polycache[0].update([(x * 32, y * 32) for x in range(33) for y in range(33)
    #                                if x in (0, 32) or y in (0, 32)])
    if lavadeath := pygame.sprite.spritecollide(plat, lavatiles, False):
        plat.die("lava", lavadeath)
    if escapes := pygame.sprite.spritecollide(plat, esctiles, False):
        fakeescapes = [s for s in escapes if type(s) != Esc]
        if len(fakeescapes) == len(escapes):
            for escape in fakeescapes:
                if isinstance(escape, Diamond):
                    escape.rect.x, escape.rect.y = -32, -32
                    for tile in esctiles:
                        if type(tile) == Esc and tile.rect.topleft == (-32, -32):
                            tile.rect.x, tile.rect.y = spawn.rect.x, spawn.rect.y
                            spawn.rect.x, spawn.rect.y = -32, -32

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
    power.conductorcache.empty()
    power.conductorcache.add([s for s in [*conductortiles, *sensortiles, *grapplertiles] if s.on])
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

    # ~20ms
    fallingtiles.update()
    conductortiles.update()
    elevtiles.update()
    switchtiles.update()
    turrettiles.update()
    pistontiles.update()
    droppertiles.update()
    conveyortiles.update()
    hooktiles.update()
    lavatiles.update()
    sensortiles.update()
    projectiles.update()
    guards.update()
    plat.move()

    # reset game window

    # ~1ms
    win = pygame.Surface((screenwidth / zoom, screenheight / zoom))
    win.fill(colors.BLACK)
    # ~5ms
    redrawgamewindow()
    # ~8ms
    screen.blit(pygame.transform.scale(pygame.transform.rotate(win, screenrotation),
                                       screen.get_size()), (0, 0))

    # print(timeit.default_timer() - start_time)
    # print(1 / (timeit.default_timer() - start_time))
    # print(f'*{clock.get_fps()}')
pygame.quit()
