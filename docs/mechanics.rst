Mechanics
=========

.. contents:: This file contains:
   :local:

Lighting
--------

:ref:`tiles:light` spawns :ref:`tiles:lighting` that runs relevant algorithms to cast
pixel-perfect shadows on nearby blocks. Information on lighting code is in :doc:`shadowcasting`.

Lighting code only affects a single object: ``shadowsurf``. This is a ``Surface`` the same size
as the screen where every pixel is either set to gray or black, then is subtracted from the screen
to create light.

The light tile is simple enough: it checks for power and spawns light on the relevant sides, much like
turrets. Lighting tiles are the ones that do most of the heavy lifting. ``Light.polycache`` is a variable
containing the results of :ref:`shadowcasting:tiletopoly()`, which is then copied to each lighting tile's
``polycache`` besides the corners contained inside the host light tile, which in turn has its results
filtered through :ref:`shadowcasting:rayvisiblecorners()`. This is now added to the lighting tile's
``visiblepolycache``, which is appended by a :ref:`shadowcasting:visibleedges()` call on itself. Afterwards,
the corners and lines are drawn and filled in on ``shadowsurf``.

Misc
----

``power()``
~~~~~~~~~~~
.. autofunction:: game.power

Checks for if a tile has power that frame.

``glitch()``
~~~~~~~~~~~~
.. autofunction:: game.glitch

``animate()``
~~~~~~~~~~~~~
.. autofunction:: game.animate

Creates an animation using in-game mechanics at the start of a select few levels. Animations
are stored inside the function.

``shake``
~~~~~~~~~
.. autofunction:: game.shake

Called to cause screenshake.

``push``
~~~~~~~~
.. autofunction:: game.push

Recursive function that handles the majority of cases where an object needs to push another.
However, for simple cases like player collision, it is not needed.

