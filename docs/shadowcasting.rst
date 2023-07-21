Shadowcasting
=============

``shadowcasting.py`` contains several methods which help to "shadowcast", a process
similar to raytracing but much faster.

.. contents:: This file contains:
    :local:
    :depth: 2

Utility
-------

Coord
~~~~~~~~~
A tuple of 2 ints.

Line
~~~~~~~~
A 2 ``Coord`` tuple.

segmentintersect()
~~~~~~~~~~~~~~~~~~~~
.. autofunction:: assets/data/shadowcasting.segmentintersect

If there are no intersections, returns a bool.
If there are infinite intersections, returns a string that evaluates to True.

checkvisible()
~~~~~~~~~~~~~~~~
.. autofunction:: assets/data/shadowcasting.checkvisible

Directions submitted must be of class Direction.

Flattening
----------

tiletopoly()
~~~~~~~~~~~~~~
.. autofunction:: assets/data/shadowcasting.tiletopoly

tiletocorners()
~~~~~~~~~~~~~~~~~
.. autofunction:: assets/data/shadowcasting.tiletocorners

Gets corners without getting edges first, meaning some corners will not be added.
Not much reason to use this.

tiletoedges()
~~~~~~~~~~~~~~~
.. autofunction:: assets/data/shadowcasting.tiletoedges

Calculation
-----------

visiblecorners()
~~~~~~~~~~~~~~~~~~
.. autofunction:: assets/data/shadowcasting.visiblecorners

rayvisiblecorners()
~~~~~~~~~~~~~~~~~~~~~
.. autofunction:: assets/data/shadowcasting.rayvisiblecorners

Upgrade of :ref:`shadowcasting:visiblecorners()` that additionally uses rays to find every point necessary

visibleedges()
~~~~~~~~~~~~~~~~
.. autofunction:: assets/data/shadowcasting.visibleedges
