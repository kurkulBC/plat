Tiles
=====

Background Tiles
-------------

Space
~~~~~
.. image:: ./assets/img/space.png
    :width: 100px
Empty space that can be passed through..

Lava
~~~~
.. image:: ./assets/img/lava.png
    :width: 100px
Kills the player on contact.

Circuit
~~~~~~~
.. image:: ./assets/img/circuit.png
    :width: 100px
The only tile :ref:`elevators <tiles:elevator>` can move on.

Generic Tiles
-------------

Block
~~~~~
.. image:: ./assets/img/block.png
    :width: 100px
Just a regular block that can be walked on and pushed. Nothing too
special.

Spawn
~~~~~
.. image:: ./assets/img/spawn.png
    :width: 100px
Where the player starts. There can only be one.

Escape
~~~~~~
.. image:: ./assets/img/escape.png
    :width: 100px
Where the player ends.

Elevator
~~~~~~~~
.. image:: ./assets/img/elevator.png
    :width: 100px
Moves along :ref:`circuits <tiles:circuit>`, Stops when powered.

Hotrock
~~~~~~~
.. image:: ./assets/img/hotrock.png
    :width: 100px
Direct source of power.

Sticky Elevator
~~~~~~~~~~~~~~~
.. image:: ./assets/img/stickyelev.png
    :width: 100px
Modification of the :ref:`elevator <tiles:elevator>` that sticks onto and drags tiles
it touches.

Diamond
~~~~~~~
.. image:: ./assets/img/diamond.png
    :width: 100px
Type of :ref:`tiles:escape`. When collected, the spawn of the level becomes an
escape.

Glass
~~~~~
.. image:: ./assets/img/glass.png
    :width: 100px
Type of :ref:`tiles:block`. Transparent.

Magma
~~~~~
.. image:: ./assets/img/lava.png
    :width: 100px
Type of :ref:`tiles:lava`. Spreads over time.

Mechanical Tiles
----------------
Switch
~~~~~~
.. image:: ./assets/img/switch.png
    :width: 100px
.. image:: ./assets/img/switch2.png
    :width: 100px
Sends out a signal of its assigned ID when pressed by the player
or a falling tile.

Door
~~~~
.. image:: ./assets/img/door.png
    :width: 100px
Toggles every time it receives a signal. While active, blocks off
all motion and power for tiles it covers.

Turret
~~~~~~
.. image:: ./assets/img/turret.png
    :width: 100px
When powered on any side, fires :ref:`bullets<tiles:bullet>` out of the opposite side
at an assigned frequency.

Light
~~~~~
.. image:: ./assets/img/stealth/light.png
    :width: 100px
When powered on any side, shines :ref:`tiles:lighting` out of the opposite side.

Piston
~~~~~~
.. image:: ./assets/img/piston.png
    :width: 100px
When powered, pushes out its :ref:`rod<tiles:piston rod>` and whatever is in front of it.

Piston Rod
~~~~~~~~~~
.. image:: ./assets/img/pistonrod.png
    :width: 100px
When powered, leaves its :ref:`tiles:piston` and pushes whatever is in front of it.

Dropper
~~~~~~~
.. image:: ./assets/img/dropper.png
    :width: 100px
When powered or signalled, releases a single :ref:`tiles:droplet`. Can only have one
active droplet.

Conveyor
~~~~~~~~
.. image:: ./assets/img/conveyor.png
    :width: 100px
When powered, pushes all low-weight tiles on it in an assigned direction.

Conductor
~~~~~~~~~
.. image:: ./assets/img/conductor.png
    :width: 100px
.. image:: ./assets/img/conductor2.png
    :width: 100px

Grappler
~~~~~~~~
.. image:: ./assets/img/grappler.png
    :width: 100px
When powered, fires out its :ref:`tiles:hook` and pulls itself to whatever it hits,
emitting power along the way

Hook
~~~~
.. image:: ./assets/img/hook.png
    :width: 100px
Fired by :ref:`grapplers<tiles:grappler>` and leaves behind a :ref:`trail<tiles:hook trail>`.

Sensor Tiles
------------

Sensor
~~~~~~
Base class of all sensors.

Transformer
~~~~~~~~~~~
.. image:: ./assets/img/transformer.png
    :width: 100px
Converts signals into power; when signalled, it switches between being a power
source and a regular tile.

Broadcaster
~~~~~~~~~~~
.. image:: ./assets/img/broadcaster.png
    :width: 100px
Converts power into signals; When it gets or loses power, it sends out a signal.

Picker
~~~~~~
.. image:: ./assets/img/picker.png
    :width: 100px
Converts droplets into signals; it consumes touching droplets and sends out a
signal whenever it does.

Tripwire
~~~~~~~~
.. image:: ./assets/img/tripwire.png
    :width: 100px
Converts motion into signals; whenever the player runs through it, it send out
a signal.

Projectiles
----------

Bullet
~~~~~~
.. image:: ./assets/img/bullet.png
    :width: 100px
Fired from :ref:`turrets<tiles:turret>`. Kills the player on hit and dies on collision with a
solid tile.

Lighting
~~~~~~~~
Casts light. Summoned from :ref:`lights<tiles:light>`.

Droplet
~~~~~~~
.. image:: ./assets/img/droplet.png
    :width: 100px
Small falling tile produced by a :ref:`tiles:dropper`. Consumed by :ref:`pickers<tiles:picker>`.

Hook Trail
~~~~~~~~~~
.. image:: ./assets/img/hook.png
    :width: 100px
Left behind by :ref:`hooks<tiles:hook>`.

Creating recipes
----------------

To retrieve a list of random ingredients,
you can use the ``lumache.get_random_ingredients()`` function:

.. autofunction:: lumache.get_random_ingredients

The ``kind`` parameter should be either ``"meat"``, ``"fish"``,
or ``"veggies"``. Otherwise, :py:func:`lumache.get_random_ingredients`
will raise an exception.

.. autoexception:: lumache.InvalidKindError

For example:

>>> import lumache
>>> lumache.get_random_ingredients()
['shells', 'gorgonzola', 'parsley']

