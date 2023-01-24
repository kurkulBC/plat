import pygame
import math
from statistics import linear_regression
from typing import Iterator


Coord = tuple[int, int]

def tiletopoly(tiles: pygame.sprite.Group) -> list[list[Coord],
        list[tuple[Coord, Coord]]]:
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

def tiletocorners(tiles: pygame.sprite.Group) -> list[Coord]:
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

def tiletoedges(tiles: pygame.sprite.Group) -> list[tuple[Coord, Coord]]:
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

def segmentintersect(line1:tuple[Coord, Coord], line2:tuple[Coord, Coord]):
    m1, b1 = linear_regression([s[0] for s in line1], [s[1] for s in line1])
    m2, b2 = linear_regression([s[0] for s in line2], [s[1] for s in line2])
    if m1 == m2:
        if b1 == b2:
            print("equal lines")
            return True
        else:
            print("parallel lines")
            return False
    x = (b2 - b1) / (m1 - m2)
    y1 = m1 * x + b1
    y2 = m2 * x + b2
    assert y1 == y2
    intersection = (int(x), int(y1))

    if intersection[0] < min(line1[0][0], line1[1][0]) or intersection[0] > max(line1[0][0], line1[1][0]):
        print('outside of line1 x')
        return False

    if intersection[1] < min(line1[0][1], line1[1][1]) or intersection[1] > max(line1[0][1], line1[1][1]):
        print('outside of line1 y')
        return False

    if intersection[0] < min(line2[0][0], line2[1][0]) or intersection[0] > max(line2[0][0], line2[1][0]):
        print('outside of line2 x')
        return False

    if intersection[1] < min(line2[0][1], line2[1][1]) or intersection[1] > max(line2[0][1], line2[1][1]):
        print('outside of line2 y')
        return False

    return intersection

def visiblepoly(start: tuple[int, int], corners: Iterator[tuple[int, int]],
        edges: Iterator[tuple[tuple[int, int], tuple[int, int]]]) -> list[tuple[int, int]]:
    visible = []
    for corner in corners:
        for edge in edges:
            if segmentintersect((start, corner), edge):
                break
        else:
            visible.append(corner)
    return visible
