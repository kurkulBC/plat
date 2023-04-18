import statistics

import pygame
from statistics import linear_regression
from typing import Iterator
from .common import width, height, size, Direction, Demo
from math import floor, ceil

Coord = tuple[int, int]
Line = tuple[Coord, Coord]


def tiletopoly(tiles: pygame.sprite.Group | Iterator[pygame.sprite.Sprite]) -> list[set[Coord], set[Line]]:
    corners = set()
    edges = set()
    for tile in tiles:
        # noinspection PyUnresolvedReferences
        coverededges = tile.coverededge()
        coveredcorners = tile.coveredcorner(coverededges)

        if hasattr(tile, 'rect'):
            if not coverededges['up'] or not coverededges['left'] or not coveredcorners['upleft']:
                corners.add((tile.rect.topleft[0] - 1, tile.rect.topleft[1] - 1))
            if not coverededges['left'] or not coverededges['down'] or not coveredcorners['downleft']:
                corners.add((tile.rect.bottomleft[0] - 1, tile.rect.bottomleft[1] + 1))
            if not coverededges['down'] or not coverededges['right'] or not coveredcorners['downright']:
                corners.add((tile.rect.bottomright[0] + 1, tile.rect.bottomright[1] + 1))
            if not coverededges['right'] or not coverededges['up'] or not coveredcorners['upright']:
                corners.add((tile.rect.topright[0] + 1, tile.rect.topright[1] - 1))

            if not coverededges['up']:
                edges.add((tile.rect.topleft, tile.rect.topright))
            if not coverededges['left']:
                edges.add((tile.rect.bottomleft, tile.rect.topleft))
            if not coverededges['down']:
                edges.add((tile.rect.bottomright, tile.rect.bottomleft))
            if not coverededges['right']:
                edges.add((tile.rect.topright, tile.rect.bottomright))

    return [list(corners), list(edges)]


def tiletocorners(tiles: pygame.sprite.Group | Iterator[pygame.sprite.Sprite]) -> set[Coord]:
    corners = set()
    for tile in tiles:
        # noinspection PyUnresolvedReferences
        coverededges = tile.coverededge()

        # the pixel diagonal to the corner so that the ray can go past
        if not coverededges[0] or not coverededges[1]:
            corners.add((tile.rect.topleft[0] - 1, tile.rect.topleft[1] - 1))
        if not coverededges[1] or not coverededges[2]:
            corners.add((tile.rect.bottomleft[0] - 1, tile.rect.bottomleft[1] + 1))
        if not coverededges[2] or not coverededges[3]:
            corners.add((tile.rect.bottomright[0] + 1, tile.rect.bottomright[1] + 1))
        if not coverededges[3] or not coverededges[0]:
            corners.add((tile.rect.topright[0] + 1, tile.rect.topright[1] - 1))

    return list(corners)


def tiletoedges(tiles: pygame.sprite.Group | Iterator[pygame.sprite.Sprite]) -> set[Line]:
    edges = set()
    for tile in tiles:
        # noinspection PyUnresolvedReferences
        coverededges = tile.coverededge()

        if not coverededges[0]:
            edges.add((tile.rect.topleft, tile.rect.topright))
        if not coverededges[1]:
            edges.add((tile.rect.bottomleft, tile.rect.topleft))
        if not coverededges[2]:
            edges.add((tile.rect.bottomright, tile.rect.bottomleft))
        if not coverededges[3]:
            edges.add((tile.rect.topright, tile.rect.bottomright))

    return list(edges)


def segmentintersect(line1: Line, line2: Line):
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


def visiblecorners(start: Coord, corners: Iterator[Coord], edges: Iterator[Line], direction: Direction = None) \
        -> list[Coord]:
    visible = []
    for corner in corners:
        if not checkvisible(start, corner, direction):
            continue

        for edge in edges:
            if segmentintersect((start, corner), edge):
                break
        else:
            visible.append(corner)
    return visible


def rayvisiblecorners(tiles: pygame.sprite.Group, hostrect: pygame.rect.Rect, start: Coord, corners: Iterator[Coord],
                      edges: Iterator[Line], direction: Direction = None) -> list[Coord]:
    corners = visiblecorners(start, corners, edges, direction)
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
    validtiles = [s for s in tiles if s.rect != hostrect]
    for corner in corners:
        vec = (pygame.math.Vector2(corner) - pygame.math.Vector2(start)).normalize()
        floatpos = list(start) + vec
        tempsprite = Demo(pygame.rect.Rect(0, 0, 1, 1))
        tempsprite.rect.center = floatpos
        while not pygame.sprite.spritecollideany(tempsprite, validtiles) and \
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
            # tempsprite.rect.center = floatpos

        # if lower than intersection, round higher, else lower
        floatpos -= vec
        # i set the positives to ceil because they didn't work otherwise
        if vec.x < 0:
            floatpos[0] = ceil(floatpos[0])
        if vec.x > 0:
            floatpos[0] = ceil(floatpos[0])
        if vec.y < 0:
            floatpos[1] = ceil(floatpos[1])
        if vec.y > 0:
            floatpos[1] = ceil(floatpos[1])
        floatpos = tuple(floatpos)
        held.append(floatpos)
        tempsprite.rect.center = hostrect.center
    # print(corners)
    return corners + held


def visibleedges(viscorners: list[Coord]) -> list[Line]:
    visible = []
    for i in range(0, len(viscorners)):
        for j in range(i + 1, len(viscorners)):
            a, b = viscorners[i], viscorners[j]
            if a[0] == b[0] and abs(a[1] - b[1]) <= size + 2 or a[1] == b[1] and abs(a[0] - b[0]) <= size + 2:
                # for corner in viscorners:
                #     # XTODO: when 2 lines are the same over a point the edge is not saved
                #     if (pos := segmentintersect((a, b), (start, corner))) and pos not in (a, b):
                #         print(pos, a, b)
                #         break
                # else:
                visible.append((a, b))

    return visible


def checkvisible(start: Coord, end: Coord, *directions: Direction) -> bool:
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

    return True
