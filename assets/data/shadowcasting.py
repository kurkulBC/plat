import statistics

import pygame
from statistics import linear_regression
from typing import Iterator
from .common import Direction

Coord = tuple[int, int]
Line = tuple[Coord, Coord]


def tiletopoly(tiles: pygame.sprite.Group | Iterator[pygame.sprite.Sprite]) -> list[list[Coord], list[Line]]:
    corners = []
    edges = []
    for tile in tiles:
        # noinspection PyUnresolvedReferences
        coverededges = tile.coverededge()

        if not coverededges[0] or not coverededges[1]:
            corners.append((tile.rect.topleft[0] - 1, tile.rect.topleft[1] - 1))
        if not coverededges[1] or not coverededges[2]:
            corners.append((tile.rect.bottomleft[0] - 1, tile.rect.bottomleft[1] + 1))
        if not coverededges[2] or not coverededges[3]:
            corners.append((tile.rect.bottomright[0] + 1, tile.rect.bottomright[1] + 1))
        if not coverededges[3] or not coverededges[0]:
            corners.append((tile.rect.topright[0] + 1, tile.rect.topright[1] - 1))

        if not coverededges[0]:
            edges.append((tile.rect.topleft, tile.rect.topright))
        if not coverededges[1]:
            edges.append((tile.rect.bottomleft, tile.rect.topleft))
        if not coverededges[2]:
            edges.append((tile.rect.bottomright, tile.rect.bottomleft))
        if not coverededges[3]:
            edges.append((tile.rect.topright, tile.rect.bottomright))

    return [corners, edges]


def tiletocorners(tiles: pygame.sprite.Group | Iterator[pygame.sprite.Sprite]) -> list[Coord]:
    corners = []
    for tile in tiles:
        # noinspection PyUnresolvedReferences
        coverededges = tile.coverededge()

        # the pixel diagonal to the corner so that the ray can go past
        if not coverededges[0] or not coverededges[1]:
            corners.append((tile.rect.topleft[0] - 1, tile.rect.topleft[1] - 1))
        if not coverededges[1] or not coverededges[2]:
            corners.append((tile.rect.bottomleft[0] - 1, tile.rect.bottomleft[1] + 1))
        if not coverededges[2] or not coverededges[3]:
            corners.append((tile.rect.bottomright[0] + 1, tile.rect.bottomright[1] + 1))
        if not coverededges[3] or not coverededges[0]:
            corners.append((tile.rect.topright[0] + 1, tile.rect.topright[1] - 1))

    return corners


def tiletoedges(tiles: pygame.sprite.Group | Iterator[pygame.sprite.Sprite]) -> list[Line]:
    edges = []
    for tile in tiles:
        # noinspection PyUnresolvedReferences
        coverededges = tile.coverededge()

        if not coverededges[0]:
            edges.append((tile.rect.topleft, tile.rect.topright))
        if not coverededges[1]:
            edges.append((tile.rect.bottomleft, tile.rect.topleft))
        if not coverededges[2]:
            edges.append((tile.rect.bottomright, tile.rect.bottomleft))
        if not coverededges[3]:
            edges.append((tile.rect.topright, tile.rect.bottomright))

    return edges


# TODO: doesn't work, always returns False
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
        print("parallel undefined lines")
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
                'equal lines'
                return True
            else:
                'parallel lines'
                return False
        x = (b2 - b1) / (m1 - m2)
        y1 = round(m1 * x + b1)
        y2 = round(m2 * x + b2)
        assert y1 == y2
        intersection = (round(x), y1)

    if intersection[0] < min(line1[0][0], line1[1][0]) or intersection[0] > max(line1[0][0], line1[1][0]):
        'at/outside of line1 domain'
        return False

    if intersection[1] < min(line1[0][1], line1[1][1]) or intersection[1] > max(line1[0][1], line1[1][1]):
        'at/outside of line1 range'
        return False

    if intersection[0] < min(line2[0][0], line2[1][0]) or intersection[0] > max(line2[0][0], line2[1][0]):
        'at/outside of line2 domain'
        return False

    if intersection[1] < min(line2[0][1], line2[1][1]) or intersection[1] > max(line2[0][1], line2[1][1]):
        'at/outside of line2 range'
        return False

    return intersection


def visiblepoly(start: Coord, corners: Iterator[Coord], edges: Iterator[Line], direction: Direction = None) \
        -> list[Coord]:
    visible = []
    for corner in corners:
        vec = pygame.math.Vector2(corner) - pygame.math.Vector2(start)
        # print(vec.normalize(), vec.angle_to(pygame.math.Vector2(-1, -1)), vec.angle_to(pygame.math.Vector2(1, -1)))
        if direction == Direction.up:
            if abs(vec.angle_to(pygame.math.Vector2(-1, -1))) > 90 or \
                    abs(vec.angle_to(pygame.math.Vector2(1, -1))) > 90:
                continue
        if direction == Direction.left:
            if 45 < abs(vec.angle_to(pygame.math.Vector2(-1, 1))) < 270 or \
                    45 < abs(vec.angle_to(pygame.math.Vector2(-1, -1))) < 270:
                continue
        if direction == Direction.down:
            if abs(vec.angle_to(pygame.math.Vector2(1, 1))) > 90 or \
                    abs(vec.angle_to(pygame.math.Vector2(-1, 1))) > 90:
                continue
        if direction == Direction.right:
            if abs(vec.angle_to(pygame.math.Vector2(1, -1))) > 90 or \
                    abs(vec.angle_to(pygame.math.Vector2(1, 1))) > 90:
                continue

        for edge in edges:
            if segmentintersect((start, corner), edge):
                break
        else:
            visible.append(corner)
    return visible
