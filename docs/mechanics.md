Mechanics
=========

Lighting
--------

[Light](tiles.md#light) spawns [Lighting](tiles.md#lighting) that runs relevant algorithms to cast
pixel-perfect shadows on nearby blocks. Information on lighting code is in [shadowcasting](shadowcasting.md).

Lighting code only affects a single object: ``shadowsurf``. This is a ``Surface`` the same size
as the screen where every pixel is either set to gray or black, then is subtracted from the screen
to create light.

The light tile is simple enough: it checks for power and spawns light on the relevant sides, much like
turrets. Lighting tiles are the ones that do most of the heavy lifting. ``Light.polycache`` is a variable
containing the results of [shadowcasting.tiletopoly()](shadowcasting.md#tiletopoly), which is then copied
to each lighting tile's ``polycache`` besides the corners contained inside the host light tile, which in turn
has its results filtered through [shadowcasting.rayvisiblecorners()](shadowcasting.md#rayvisiblecorners). 
This is now added to the lighting tile's ``visiblepolycache``, which is appended by a 
[shadowcasting.visibleedges()](shadowcasting.md#visibleedges) call on itself. Afterwards, the corners and lines 
are drawn and filled in on ``shadowsurf``.

Misc
----

### power()
#### ::: game.power

Checks for if a tile has power that frame.

### glitch()
#### ::: game.glitch

### animate()
#### ::: game.animate

Creates an animation using in-game mechanics at the start of a select few levels. Animations
are stored inside the function.

### shake()
#### ::: game.shake

Called to cause screenshake.

### push()
#### ::: game.push

Recursive function that handles the majority of cases where an object needs to push another.
However, for simple cases like player collision, it is not needed.

