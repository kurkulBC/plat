import statistics

import pygame
from statistics import linear_regression
from typing import Iterator
from .common import width, height, size, Direction, Demo
from math import floor, ceil

Coord = tuple[int, int]
Line = tuple[Coord, Coord]


def tiletopoly(tiles: pygame.sprite.Group | Iterator[pygame.sprite.Sprite]) -> list[set[Coord], set[Line]]:
    """
    :param tiles: a tile group
    :return: the visible corners and edges of the tiles
    """
    corners = set()
    edges = set()
    for tile in tiles:
        # noinspection PyUnresolvedReferences
        coverededges = tile.coverededge()
        coveredcorners = tile.coveredcorner(coverededges)

        if hasattr(tile, 'rect'):
            if not coverededges['up']:
                edges.add((tile.rect.topleft, tile.rect.topright))
            if not coverededges['left']:
                edges.add((tile.rect.bottomleft, tile.rect.topleft))
            if not coverededges['down']:
                edges.add((tile.rect.bottomright, tile.rect.bottomleft))
            if not coverededges['right']:
                edges.add((tile.rect.topright, tile.rect.bottomright))

            if not coveredcorners['upleft']:
                corners.add((tile.rect.topleft[0] - 1, tile.rect.topleft[1] - 1))
            if not coveredcorners['downleft']:
                corners.add((tile.rect.bottomleft[0] - 1, tile.rect.bottomleft[1] + 1))
            if not coveredcorners['downright']:
                corners.add((tile.rect.bottomright[0] + 1, tile.rect.bottomright[1] + 1))
            if not coveredcorners['upright']:
                corners.add((tile.rect.topright[0] + 1, tile.rect.topright[1] - 1))

            if tile.rect.left <= 0:
                corners.add((0, tile.rect.top - 1))
                corners.add((0, tile.rect.bottom + 1))
            elif tile.rect.right >= width:
                corners.add((width, tile.rect.top - 1))
                corners.add((width, tile.rect.bottom + 1))
            if tile.rect.top <= 0:
                corners.add((tile.rect.left - 1, 0))
                corners.add((tile.rect.right + 1, 0))
            elif tile.rect.bottom >= height:
                corners.add((tile.rect.left - 1, height))
                corners.add((tile.rect.right + 1, height))

    return [corners, tiletoedges(tiles)]


def tiletocorners(tiles: pygame.sprite.Group | Iterator[pygame.sprite.Sprite]) -> set[Coord]:
    """
    :param tiles: a tile group
    :return: the visible corners of the tiles
    """
    corners = set()
    for tile in tiles:
        coverededges = tile.coverededge()

        # the pixel diagonal to the corner so that the ray can go past
        if not coverededges['up'] and not coverededges['left']:
            corners.add((tile.rect.topleft[0] - 1, tile.rect.topleft[1] - 1))
        if not coverededges['left'] and not coverededges['down']:
            corners.add((tile.rect.bottomleft[0] - 1, tile.rect.bottomleft[1] + 1))
        if not coverededges['down'] and not coverededges['right']:
            corners.add((tile.rect.bottomright[0] + 1, tile.rect.bottomright[1] + 1))
        if not coverededges['right'] and not coverededges['up']:
            corners.add((tile.rect.topright[0] + 1, tile.rect.topright[1] - 1))

    return corners


def tiletoedges(tiles: pygame.sprite.Group | Iterator[pygame.sprite.Sprite]) -> set[Line]:
    """
    :param tiles: a tile group
    :return: the visible edges of the tiles
    """
    edges = set()
    for tile in tiles:
        coverededges = tile.coverededge()

        if not coverededges['up']:
            edges.add((tile.rect.topleft, tile.rect.topright))
        if not coverededges['left']:
            edges.add((tile.rect.bottomleft, tile.rect.topleft))
        if not coverededges['down']:
            edges.add((tile.rect.bottomright, tile.rect.bottomleft))
        if not coverededges['right']:
            edges.add((tile.rect.topright, tile.rect.bottomright))

    return edges


def segmentintersect(line1: Line, line2: Line) -> Coord | bool | str:
    """
    :param line1: The first line
    :param line2: The second line
    :return: The intersection of the lines if there is exactly 1.
    """
    m1 = m2 = b1 = b2 = None

    try:
        m1, b1 = linear_regression([s[0] for s in line1], [s[1] for s in line1])
    except statistics.StatisticsError:
        pass
    try:
        m2, b2 = linear_regression([s[0] for s in line2], [s[1] for s in line2])
    except statistics.StatisticsError:
        pass

    if m1 is None and m2 is None:
        if line1[0][0] == line2[0][0]:
            return 'equal lines'
        else:
            'parallel undefined lines'
            return False

    if m1 is None:
        x = line1[0][0]
        y2 = m2 * x + b2
        intersection = (int(x), int(y2))
    elif m2 is None:
        x = line2[0][0]
        y1 = m1 * x + b1
        intersection = (int(x), int(y1))

    else:
        if m1 == m2:
            if b1 == b2:
                return 'equal lines'
            else:
                'parallel lines'
                return False
        x = (b2 - b1) / (m1 - m2)
        y1 = round(m1 * x + b1)
        y2 = round(m2 * x + b2)
        assert y1 == y2
        intersection = (round(x), y1)

    if intersection[0] < min(line1[0][0], line1[1][0]) or intersection[0] > max(line1[0][0], line1[1][0]):
        'outside of line1 domain'
        return False

    if intersection[1] < min(line1[0][1], line1[1][1]) or intersection[1] > max(line1[0][1], line1[1][1]):
        'outside of line1 range'
        return False

    if intersection[0] < min(line2[0][0], line2[1][0]) or intersection[0] > max(line2[0][0], line2[1][0]):
        'outside of line2 domain'
        return False

    if intersection[1] < min(line2[0][1], line2[1][1]) or intersection[1] > max(line2[0][1], line2[1][1]):
        'outside of line2 range'
        return False

    return intersection


# TODO: map borders not in corners
def visiblecorners(start: Coord, corners: Iterator[Coord], edges: Iterator[Line], tiles=None,
                   direction: Direction = None) -> list[Coord]:
    """
    :param start: The start coordinate
    :param corners: The corners to be checked
    :param edges: The edges to be checked
    :param tiles: The tiles to be submitted to checkvisible
    :param direction: The direction to check
    :return: Every corner in the given corners that is visible to the start coordinate
    in the given direction
    """
    visible = []
    for corner in corners:
        if not checkvisible(start, corner, direction, tiles=tiles):
            continue

        for edge in edges:
            if segmentintersect((start, corner), edge):
                break
        else:
            visible.append(corner)
    return visible


def rayvisiblecorners(tiles: pygame.sprite.Group, hostrect: pygame.rect.Rect, start: Coord, corners: Iterator[Coord],
                      edges: Iterator[Line], direction: Direction = None) -> list[Coord]:
    """
    :param tiles: The tiles to use for collision
    :param hostrect: The rect of the producing light tile
    :param start: The start coordinate
    :param corners: The corners to be checked
    :param edges: The edges to be checked
    :param direction: The direction to check
    :return: Every corner in the given corners that is visible to the start coordinate
    in the given direction, alongside coordinates of where light going past corners hits
    """
    corners = visiblecorners(start, corners, edges, tiles, direction)
    if direction == Direction.up:
        corners.append(hostrect.topright)
        corners.append(hostrect.topleft)
    if direction == Direction.left:
        corners.append(hostrect.topleft)
        corners.append(hostrect.bottomleft)
    if direction == Direction.down:
        corners.append(hostrect.bottomleft)
        corners.append(hostrect.bottomright)
    if direction == Direction.right:
        corners.append(hostrect.bottomright)
        corners.append(hostrect.topright)
    held = []
    validtiles = [s for s in tiles if s.rect is not hostrect]
    for corner in corners:
        vec = (pygame.math.Vector2(corner) - pygame.math.Vector2(start)).normalize()
        # vec.scale_to_length(size - 1)
        floatpos = list(corner)
        tempsprite = Demo(pygame.rect.Rect(0, 0, 1, 1))
        tempsprite.rect.center = floatpos
        while not (collision := pygame.sprite.spritecollideany(tempsprite, validtiles)) and \
                0 <= floatpos[0] <= width and 0 <= floatpos[1] <= height:
            floatpos += vec
            if vec.x < 0:
                tempsprite.rect.centerx = floor(floatpos[0])
            if vec.x > 0:
                tempsprite.rect.centerx = ceil(floatpos[0])
            if vec.y < 0:
                tempsprite.rect.centery = floor(floatpos[1])
            if vec.y > 0:
                tempsprite.rect.centery = ceil(floatpos[1])

        # noinspection PyShadowingNames
        def collidecheck(start, floatpos, vec, collision):
            if vec.x < 0:
                if collision:
                    point = segmentintersect((start, floatpos), ((collision.rect.bottom + 1, collision.rect.right + 1),
                                                                 (collision.rect.top - 1, collision.rect.right + 1)))
                    if isinstance(point, tuple):
                        return point
                elif floatpos[0] < 1:
                    floatpos[0] = 1
            elif vec.x > 0:
                if collision:
                    point = segmentintersect((start, floatpos), ((collision.rect.top - 1, collision.rect.left - 1),
                                                                 (collision.rect.bottom + 1, collision.rect.left - 1)))
                    if isinstance(point, tuple):
                        return point
                elif floatpos[0] > width - 1:
                    floatpos[0] = width - 1
            if vec.y < 0:
                if collision:
                    point = segmentintersect((start, floatpos), ((collision.rect.bottom + 1, collision.rect.left - 1),
                                                                 (collision.rect.bottom + 1, collision.rect.right + 1)))
                    if isinstance(point, tuple):
                        return point
                elif floatpos[1] < 1:
                    floatpos[1] = 1
            elif vec.y > 0:
                if collision:
                    point = segmentintersect((start, floatpos), ((collision.rect.top - 1, collision.rect.right + 1),
                                                                 (collision.rect.top - 1, collision.rect.left - 1)))
                    if isinstance(point, tuple):
                        return point
                elif floatpos[1] > height - 1:
                    floatpos[1] = height - 1
            return [round(floatpos[0]), round(floatpos[1])]

        held.append(tuple(collidecheck(start, floatpos, vec, collision)))
    # print(corners)
    return corners + held


def visibleedges(viscorners: list[Coord]) -> list[Line]:
    """
    :param viscorners: corners that are visible to the source
    :return: list of all horizontal and vertical lines that are visible to the source
    """
    visible = []
    for i in range(0, len(viscorners)):
        for j in range(i + 1, len(viscorners)):
            a, b = viscorners[i], viscorners[j]
            if a[0] == b[0] and abs(a[1] - b[1]) <= size + 2 or a[1] == b[1] and abs(a[0] - b[0]) <= size + 2:
                visible.append((a, b))

    return visible


def checkvisible(start: Coord, end: Coord, *directions: Direction, tiles: pygame.sprite.Group = None) -> bool:
    """
    :param start: The start coordinate
    :param end: The desired end coordinate
    :param directions: A list of directions to check for visibility in
    :param tiles: optional parameter that, if not None, will evaluate every tile inside for collisions
    :return: Whether the end is visible from the start in every direction given
    """
    up = pygame.math.Vector2(0, -1)
    left = pygame.math.Vector2(-1, 0)
    down = pygame.math.Vector2(0, 1)
    right = pygame.math.Vector2(1, 0)

    upleft = pygame.math.Vector2(-1, -1)
    downleft = pygame.math.Vector2(-1, 1)
    downright = pygame.math.Vector2(1, 1)
    upright = pygame.math.Vector2(1, -1)

    vec = pygame.math.Vector2(end) - pygame.math.Vector2(start)

    if Direction.up in directions:
        if abs(vec.angle_to(upleft)) > 91 or \
                abs(vec.angle_to(upright)) > 91:
            return False
    if Direction.left in directions:
        if 46 < abs(vec.angle_to(downleft)) < 269 or \
                46 < abs(vec.angle_to(upleft)) < 269:
            return False
    if Direction.down in directions:
        if abs(vec.angle_to(downright)) > 91 or \
                abs(vec.angle_to(downleft)) > 91:
            return False
    if Direction.right in directions:
        if abs(vec.angle_to(upright)) > 91 or \
                abs(vec.angle_to(downright)) > 91:
            return False

    if Direction.upleft in directions:
        if abs(vec.angle_to(up)) > 91 or \
                abs(vec.angle_to(left)) > 91:
            return False
    if Direction.downleft in directions:
        if abs(vec.angle_to(left)) > 91 or \
                91 < abs(vec.angle_to(down)) < 269:
            return False
    if Direction.downright in directions:
        if 91 < abs(vec.angle_to(down)) < 269 or \
                abs(vec.angle_to(right)) > 91:
            return False
    if Direction.upright in directions:
        if abs(vec.angle_to(right)) > 91 or \
                abs(vec.angle_to(up)) > 91:
            return False

    if tiles:
        for tile in tiles:
            if tile.rect.clipline(start, end) and type(tile).__name__ not in ("Light", "Glass"):
                return False

    return True
