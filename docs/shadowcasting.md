Shadowcasting
=============

``shadowcasting.py`` contains several methods which help to "shadowcast", a process
similar to raytracing but much faster.

Utility
-------

### Coord
A tuple of 2 ints.

### Line
A 2 [Coord](#Coord) tuple.

### ``segmentintersect()``
#### ::: assets.data.shadowcasting.segmentintersect

Returns the intersection of the lines if there is exactly 1.
If there are no intersections, returns a bool.
If there are infinite intersections, returns a string that evaluates to True.

### ``checkvisible()``
#### ::: assets.data.shadowcasting.checkvisible

Returns whether the end is visible from the start in every direction given.
Directions submitted must be of class Direction.

Flattening
----------

### ``tiletopoly()``
#### ::: assets.data.shadowcasting.tiletopoly

Returns the visible corners and edges of the tiles.

### ``tiletocorners()``
#### ::: assets.data.shadowcasting.tiletocorners

Returns the visible corners of the tiles.
Gets corners without getting edges first, meaning some corners will not be added.
Not much reason to use this.

### ``tiletoedges()``
#### ::: assets.data.shadowcasting.tiletoedges

Returns the visible edges of the tiles.

Calculation
-----------

### ``visiblecorners()``
#### ::: assets.data.shadowcasting.visiblecorners

Returns every corner in the given corners that is visible to the start coordinate in a 90 degree cone
of the given direction.

### ``rayvisiblecorners()``
#### ::: assets.data.shadowcasting.rayvisiblecorners

Returns every corner in the given corners that is visible to the start coordinate in the given direction, 
alongside coordinates of where light rays hit.
Upgrade of :ref:`shadowcasting:visiblecorners()``` that additionally uses rays to find every point necessary.

### ``visibleedges()``
#### ::: assets.data.shadowcasting.visibleedges

Returns a list of all tile edges that are visible to the source.
