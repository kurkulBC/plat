Tiles
=====

Background Tiles
----------------

### Space
<img src="../img/space.png" width="100"/>

Empty space that can be passed through.

### Lava
<img src="../img/lava.png" width="100"/>

Kills the player on contact.

### Circuit
<img src="../img/circuit.png" width="100"/>

The only tile [elevators](#elevator) can move on.

Generic Tiles
-------------

### Block
<img src="../img/block.png" width="100"/>

Just a regular block that can be walked on and pushed. Nothing too
special.

### Spawn
<img src="../img/spawn.png" width="100"/>

Where the player starts. There can only be one.

### Escape
<img src="../img/escape.png" width="100"/>

Where the player ends.

### Elevator
<img src="../img/elevator.png" width="100"/>

Moves along [circuits](#circuit), Stops when powered.

### Hotrock
<img src="../img/hotrock.png" width="100"/>

Direct source of power.

### Sticky Elevator
<img src="../img/stickyelevator.png" width="100"/>

Modification of the [elevator](#elevator) that sticks onto and drags tiles
it touches.

### Diamond
<img src="../img/stealth/diamond.png" width="100"/>

Type of [escape](#escape). When collected, the spawn of the level becomes an
escape.

### Glass
<img src="../img/stealth/glass.png" width="100"/>

Type of [block](#block). Transparent.

### Magma
<img src="../img/lava.png" width="100"/>

Type of [lava](#lava). Spreads over time.

Mechanical Tiles
----------------
### Switch
<img src="../img/switch.png" width="100"/>
<img src="../img/switch2.png" width="100"/>

Sends out a signal of its assigned ID when pressed by the player
or a falling tile.

### Door
<img src="../img/door.png" width="100"/>

Toggles every time it receives a signal. While active, blocks off
all motion and power for tiles it covers.

### Turret
<img src="../img/turret.png" width="100"/>

When powered on any side, fires [bullets](#bullet) out of the opposite side
at an assigned frequency.

### Light
<img src="../img/stealth/light.png" width="100"/>

When powered on any side, shines [lighting](#lighting) out of the opposite side.

### Piston
<img src="../img/piston.png" width="100"/>

When powered, pushes out its [piston rod](#piston-rod) and whatever is in front of it.

### Piston Rod
<img src="../img/pistonrod.png" width="100"/>

When powered, leaves its [piston](#piston) and pushes whatever is in front of it.

### Dropper
<img src="../img/dropper.png" width="100"/>

When powered or signalled, releases a single [droplet](#droplet). Can only have one
active droplet.

### Conveyor
<img src="../img/conveyor.png" width="100"/>

When powered, pushes all low-weight tiles on it in an assigned direction.

### Conductor
<img src="../img/conductor.png" width="100"/>
<img src="../img/conductor2.png" width="100"/>

Emits power when powered externally, otherwise inert

### Grappler
<img src="../img/grappler.png" width="100"/>

When powered, fires out its [hook](#hook) and pulls itself to whatever it hits,
emitting power along the way

### Hook
<img src="../img/hook.png" width="100"/>

Fired by [grapplers](#grappler) and leaves behind a [trail](#hook-trail).

Sensor Tiles
------------

### Sensor
Base class of all sensors.

### Transformer
<img src="../img/transformer.png" width="100"/>

Converts signals into power; when signalled, it switches between being a power
source and a regular tile.

### Broadcaster
<img src="../img/broadcaster.png" width="100"/>

Converts power into signals; When it gets or loses power, it sends out a signal.

### Picker
<img src="../img/picker.png" width="100"/>

Converts droplets into signals; it consumes touching droplets and sends out a
signal whenever it does.

### Tripwire
<img src="../img/tripwire.png" width="100"/>
<img src="../img/tripwire2.png" width="100"/>

Converts motion into signals; whenever the player runs through it, it send out
a signal.

Projectiles
-----------

### Bullet
<img src="../img/bullet.png" width="100"/>

Fired from [turrets](#turret). Kills the player on hit and dies on collision with a
solid tile.

### Lighting
Casts light. Summoned from [lights](#light).

### Droplet
<img src="../img/droplet.png" width="100"/>

Small falling tile produced by a [dropper](#dropper). Consumed by [pickers](#picker).

### Hook Trail
<img src="../img/hooktrail.png" width="100"/>

Left behind by [hooks](#hook).

