import statistics

import pygame
from statistics import linear_regression
from typing import Iterator, Set, Tuple, Type

import assets.data.common
from .common import width, height, size, Direction, Demo
from math import floor, ceil
from enum import Flag, auto

Coord = tuple[int, int]
Line = tuple[Coord, Coord]


class LightingManager:
    class Direction(Flag):
        NONE = 0
        TOP = auto()
        BOTTOM = auto()
        LEFT = auto()
        RIGHT = auto()
        TOPLEFT = auto()
        BOTTOMLEFT = auto()
        TOPRIGHT = auto()
        BOTTOMRIGHT = auto()
        ALL = TOP | BOTTOM | LEFT | RIGHT | TOPLEFT | BOTTOMLEFT | TOPRIGHT | BOTTOMRIGHT

    static_tiles: pygame.sprite.Group | Iterator[pygame.sprite.Sprite]
    dynamic_tiles: pygame.sprite.Group | Iterator[pygame.sprite.Sprite]
    off_grid_entities: pygame.sprite.Group | Iterator[pygame.sprite.Sprite]
    light_sources = list(tuple[Coord, Direction])

    level_data: list
    static_tiles_mask = set([1, 9, 16])
    dynamic_tiles_mask = set([3])

    static_polygons: list[list[Coord]]

    @staticmethod
    def get_unique_corners(tiles: pygame.sprite.Group | Iterator[pygame.sprite.Sprite], tile_mask: set[int]) -> set[Coord]:
        corners: set[Coord]
        corners = set()

        map_size = (len(LightingManager.level_data[0]), len(LightingManager.level_data))
        for tile in tiles:
            # checking what sides/corners of the tile are covered using level_data as a grid
            # should only be used for in-grid tiles
            grid_pos = (tile.rect.topleft[0] // size, tile.rect.topleft[1] // size)
            coverage = LightingManager.Direction.NONE
            border_coverage = LightingManager.Direction.NONE

            # TODO: this if-else chain is making me nauseous. please do something with it
            # checking if the tile itself is allowed by the mask
            if not ((type(LightingManager.level_data[grid_pos[1]][grid_pos[0]]) is int)\
                    and (LightingManager.level_data[grid_pos[1]][grid_pos[0]] in tile_mask)):
                coverage = LightingManager.Direction.ALL
            # checking what sides/corners of the tile are covered
            elif grid_pos[0] > 0:     # x-1
                if grid_pos[1] > 0:     # x-1, y-1
                    if (type(LightingManager.level_data[grid_pos[1] - 1][grid_pos[0] - 1]) is int)\
                            and (LightingManager.level_data[grid_pos[1] - 1][grid_pos[0] - 1] in tile_mask):
                        coverage |= LightingManager.Direction.TOPLEFT
                else:
                    coverage |= LightingManager.Direction.TOPLEFT

                if (type(LightingManager.level_data[grid_pos[1]][grid_pos[0] - 1]) is int)\
                        and (LightingManager.level_data[grid_pos[1]][grid_pos[0] - 1] in tile_mask):    #x-1, y
                    coverage |= LightingManager.Direction.LEFT

                if grid_pos[1] < (map_size[1] - 1):     # x-1, y+1
                    if (type(LightingManager.level_data[grid_pos[1] + 1][grid_pos[0] - 1]) is int)\
                            and (LightingManager.level_data[grid_pos[1] + 1][grid_pos[0] - 1] in tile_mask):
                        coverage |= LightingManager.Direction.BOTTOMLEFT
                else:
                    coverage |= LightingManager.Direction.BOTTOMLEFT
            else:
                border_coverage |= LightingManager.Direction.TOPLEFT | LightingManager.Direction.LEFT | LightingManager.Direction.BOTTOMLEFT

            if grid_pos[1] > 0:  # x, y-1
                if (type(LightingManager.level_data[grid_pos[1] - 1][grid_pos[0]]) is int)\
                        and (LightingManager.level_data[grid_pos[1] - 1][grid_pos[0]] in tile_mask):
                    coverage |= LightingManager.Direction.TOP
            else:
                coverage |= LightingManager.Direction.TOP
                border_coverage |= LightingManager.Direction.TOP

            if grid_pos[1] < (map_size[1] - 1):  # x, y+1
                if (type(LightingManager.level_data[grid_pos[1] + 1][grid_pos[0]]) is int):
                    if (LightingManager.level_data[grid_pos[1] + 1][grid_pos[0]] in tile_mask):
                        coverage |= LightingManager.Direction.BOTTOM
            else:
                border_coverage |= LightingManager.Direction.BOTTOM

            if grid_pos[0] < (map_size[0] - 1):     # x+1
                if grid_pos[1] > 0:     # x+1, y-1
                    if (type(LightingManager.level_data[grid_pos[1] - 1][grid_pos[0] + 1]) is int)\
                            and (LightingManager.level_data[grid_pos[1] - 1][grid_pos[0] + 1] in tile_mask):
                        coverage |= LightingManager.Direction.TOPRIGHT
                else:
                    coverage |= LightingManager.Direction.TOPRIGHT

                if (type(LightingManager.level_data[grid_pos[1]][grid_pos[0] + 1]) is int)\
                        and (LightingManager.level_data[grid_pos[1]][grid_pos[0] + 1] in tile_mask):    # x+1, y
                    coverage |= LightingManager.Direction.RIGHT

                if grid_pos[1] < (map_size[1] - 1):     # x+1, y+1
                    if (type(LightingManager.level_data[grid_pos[1] + 1][grid_pos[0] + 1]) is int)\
                            and (LightingManager.level_data[grid_pos[1] + 1][grid_pos[0] + 1] in tile_mask):
                        coverage |= LightingManager.Direction.BOTTOMRIGHT
                else:
                    coverage |= LightingManager.Direction.BOTTOMRIGHT
            else:
                border_coverage |= LightingManager.Direction.TOPRIGHT | LightingManager.Direction.RIGHT | LightingManager.Direction.BOTTOMRIGHT

            if coverage | border_coverage == LightingManager.Direction.ALL:
                coverage = LightingManager.Direction.ALL


            # selecting "unique" corners
            #
            #   ###o### - 'o' adds no details to the polygon. Not unique
            #
            #   ##o     - 'o' is acting as a corner. Is necessary to build proper shadows. Top-right corner is unique
            #   ###
            #
            #   ##      - 'o' is acting as an inner corner. Top-right corner is unique again
            #   #o###
            #
            tl = LightingManager.Direction.LEFT | LightingManager.Direction.TOP
            if (tl & coverage == LightingManager.Direction.NONE) \
                    or (tl in coverage and LightingManager.Direction.TOPLEFT not in coverage):
                corners.add((tile.rect.topleft[0], tile.rect.topleft[1]))

            tr = LightingManager.Direction.RIGHT | LightingManager.Direction.TOP
            if (tr & coverage == LightingManager.Direction.NONE) \
                    or (tr in coverage and LightingManager.Direction.TOPRIGHT not in coverage):
                corners.add((tile.rect.topright[0], tile.rect.topright[1]))

            bl = LightingManager.Direction.LEFT | LightingManager.Direction.BOTTOM
            if (bl & coverage == LightingManager.Direction.NONE) \
                    or (bl in coverage and LightingManager.Direction.BOTTOMLEFT not in coverage):
                corners.add((tile.rect.bottomleft[0], tile.rect.bottomleft[1]))

            br = LightingManager.Direction.RIGHT | LightingManager.Direction.BOTTOM
            if (br & coverage == LightingManager.Direction.NONE) \
                    or (br in coverage and LightingManager.Direction.BOTTOMRIGHT not in coverage):
                corners.add((tile.rect.bottomright[0], tile.rect.bottomright[1]))

        return corners

    @staticmethod
    def get_visible_corners(light_source: tuple[Coord, Direction], corners: set[Coord], tile_mask: set[int]) -> list[tuple[Coord, float]]:
        pos = light_source[0]
        dir = light_source[1]
        visible_corners: list[tuple[Coord,float]]
        visible_corners = []

        # get light source direction vector
        fov_vec: tuple[float, float]
        if dir == Direction.up:
            fov_vec = (0, -1)
        elif dir == Direction.down:
            fov_vec = (0, 1)
        elif dir == Direction.left:
            fov_vec = (-1, 0)
        else:  # if dir == Direction.right:
            fov_vec = (1, 0)

        for corner in corners:
            # get vector connecting light source and a corner and normalize it
            delta = (corner[0] - pos[0], corner[1] - pos[1])
            delta_len = math.sqrt(delta[0]*delta[0]+delta[1]*delta[1])
            delta_norm = (delta[0] / delta_len, delta[1] / delta_len)
            # check if the angle between FOV vector and direction vector is less than 45*
            # (there's a different way to do this check that doesn't involve normalization, but it also won't yield a sine)
            # (and sine will be necessary to build a polygon later)
            ang_cos: float
            ang_cos = delta_norm[0] * fov_vec[0] + delta_norm[1] * fov_vec[1]
            # (technically, it's checking if the angle is less than ~44,7*)
            # (this difference won't be noticed by players, but it will prevent lone strips of light from appearing)
            if ang_cos > 0.71:
                ang_sin: float
                ang_sin = delta_norm[0] * fov_vec[1] + delta_norm[1] * (-1) * fov_vec[0]
                # ...and if it is, send a ray to the corner

                if(corner[0] == 800) and (corner[1] == 736):
                    pass
                hit = LightingManager.tiled_raycast(light_source[0], delta_norm, len(LightingManager.level_data), tile_mask)

                # checking if the ray has hit its target.
                # if not, the hit point is useless and will only clutter the list
                delta_hit = (hit[0] - corner[0], hit[1] - corner[1])
                imp_delta = delta_hit[0] * fov_vec[0] + delta_hit[1] * fov_vec[1]
                if imp_delta > -1 * (assets.data.common.size // 2):
                    visible_corners.append((hit, ang_sin))
                    # if the ray hit the corner, went through it and then hit something else,
                    # the corner should still be added to the list
                    if imp_delta > (assets.data.common.size // 2):
                        # for polygon to be built correctly, no two points in the list
                        # should have same ang_sin, so small angular shift should be applied
                        #     \  #/
                        #     #\ /          in all of the shown cases there should be a clockwise shift
                        #       *           and counter-clockwise shift in the rest
                        #      / \#
                        #     /#  \
                        # getting location of the target corner on a tile:
                        # TODO: same ugly code as in get_unique_corners. there should be a neat way to do this...
                        grid_pos = ((corner[0] - 10) // size, (corner[1] - 10) // size)
                        corner_type = LightingManager.Direction.NONE
                        if (type(LightingManager.level_data[grid_pos[1]][grid_pos[0]]) is int) \
                            and (LightingManager.level_data[grid_pos[1]][grid_pos[0]] in tile_mask):
                            corner_type |= LightingManager.Direction.BOTTOMRIGHT
                        if (type(LightingManager.level_data[grid_pos[1] + 1][grid_pos[0]]) is int) \
                            and (LightingManager.level_data[grid_pos[1] + 1][grid_pos[0]] in tile_mask):
                            corner_type |= LightingManager.Direction.TOPRIGHT
                        if (type(LightingManager.level_data[grid_pos[1]][grid_pos[0] + 1]) is int) \
                            and (LightingManager.level_data[grid_pos[1]][grid_pos[0] + 1] in tile_mask):
                            corner_type |= LightingManager.Direction.BOTTOMLEFT
                        if (type(LightingManager.level_data[grid_pos[1] + 1][grid_pos[0] + 1]) is int) \
                            and (LightingManager.level_data[grid_pos[1] + 1][grid_pos[0] + 1] in tile_mask):
                            corner_type |= LightingManager.Direction.TOPLEFT

                        shift: float
                        if delta_norm[0] > 0: # right semicircle
                            if delta_norm[1] < 0: # top-right pie
                                if LightingManager.Direction.BOTTOMRIGHT in corner_type:
                                    shift = 1
                                else:
                                    shift = -1
                            else: # bottom-right pie
                                if LightingManager.Direction.BOTTOMLEFT in corner_type:
                                    shift = 1
                                else:
                                    shift = -1
                        else: # left semicircle
                            if delta_norm[1] > 0: # bottom-left pie
                                if LightingManager.Direction.TOPLEFT in corner_type:
                                    shift = -1
                                else:
                                    shift = 1
                            else: # top-left pie
                                if LightingManager.Direction.TOPRIGHT in corner_type:
                                    shift = -1
                                else:
                                    shift = 1

                        shift *= ang_sin / abs(delta[1] * delta[0])
                        visible_corners.append((corner, ang_sin + shift))

                        # FIXME: there's an edge case that i'm not checking for: (or corner case, hehe)
                        #  \#
                        #  #\
                        #  the ray will go right through any two diagonal tiles
                        #  and even angular shift will be applied to make things look much worse visually
                        #  however i don't think there's currently a level that can trigger such behaviour

        # sending rays to the FOV edges
        # rotating FOV vector by ~45* to get edge vectors
        edge_a = (fov_vec[0] * 0.71 - fov_vec[1] * -0.7042, fov_vec[0] * -0.7042 + fov_vec[1] * 0.71)
        edge_b = (fov_vec[0] * 0.71 - fov_vec[1] * 0.7042, fov_vec[0] * 0.7042 + fov_vec[1] * 0.71)

        hit_a = LightingManager.tiled_raycast(light_source[0], edge_a, assets.data.common.screenwidth, tile_mask)
        hit_b = LightingManager.tiled_raycast(light_source[0], edge_b, assets.data.common.screenwidth, tile_mask)

        visible_corners.append((hit_a, 0.7042))
        visible_corners.append((hit_b, -0.7042))

        return visible_corners

    @staticmethod
    def tiled_raycast(start_point: Coord, direction_normvec: tuple[float, float], max_depth: int, tile_mask: set[int]) -> Coord:
        # this raycasting method should only be used for in-grid tiles
        # direction vector is expected to be normalized externally
        int_dir = (int(math.copysign(1, direction_normvec[0])), int(math.copysign(1, direction_normvec[1])))

        hitf_x = start_point[0]
        hitf_y = start_point[1]
        tile_x = start_point[0] // size
        tile_y = start_point[1] // size
        tile_targ_x = tile_x
        tile_targ_y = tile_y
        if(int_dir[0] > 0):
            tile_targ_x+=1
        if(int_dir[1] > 0):
            tile_targ_y+=1

        for depth in range(1, max_depth):
            dist_steps_x = (tile_targ_x * size - hitf_x) / direction_normvec[0]
            dist_steps_y = (tile_targ_y * size - hitf_y) / direction_normvec[1]
            if dist_steps_x < dist_steps_y:
                tile_x += int_dir[0]
                tile_targ_x += int_dir[0]
                hitf_x += direction_normvec[0] * dist_steps_x
                hitf_y += direction_normvec[1] * dist_steps_x
            else:
                tile_y += int_dir[1]
                tile_targ_y += int_dir[1]
                hitf_y += direction_normvec[1] * dist_steps_y
                hitf_x += direction_normvec[0] * dist_steps_y

            if (tile_y >= len(LightingManager.level_data)) or tile_y < 0:
                break
            if tile_x >= len(LightingManager.level_data[0]) or tile_x < 0:
                break

            tile = LightingManager.level_data[tile_y][tile_x]
            if type(tile) is int:
                if tile in tile_mask:
                    if abs(dist_steps_x - dist_steps_y) > 0.1: # letting rays go through the corners
                        break

        hit = (int(hitf_x), int(hitf_y))
        return hit

    @staticmethod
    def corners_to_poly(corner_tuples: list[tuple[Coord,float]], source_center: Coord):
        srtd = sorted(corner_tuples, key=lambda corner: corner[1])
        polygon = list(map(lambda corner: corner[0], srtd))
        polygon.append(source_center)
        return polygon

    @staticmethod
    def update_static_tiles():
        dtime_start = pygame.time.get_ticks() # DEBUG
        LightingManager.static_polygons = list()
        corners = LightingManager.get_unique_corners(LightingManager.static_tiles, LightingManager.static_tiles_mask)
        dtime_ucorners = pygame.time.get_ticks() # DEBUG
        dtime_sources = list() # DEBUG
        for source in LightingManager.light_sources:
            visible_corners = LightingManager.get_visible_corners(source, corners, LightingManager.static_tiles_mask)
            poly = LightingManager.corners_to_poly(visible_corners, source[0])
            LightingManager.static_polygons.append(poly)
            dtime_sources.append(pygame.time.get_ticks()) # DEBUG

        print("start time:\t\t" + str(dtime_start)) # DEBUG
        print("getting unique corners:\t" + str(dtime_ucorners - dtime_start)) # DEBUG
        for i in range(len(dtime_sources)): # DEBUG
            print("source #" + str(i) + ":\t\t" + str(dtime_sources[i] - dtime_start)) # DEBUG
        print("finish time:\t\t" + str(dtime_sources[-1])) # DEBUG


# TODO: remove all the old code below

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
