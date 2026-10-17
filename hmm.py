"""decompile_rbsp.geoset_primitives optimisation lab"""
import collections
import functools
from typing import Set, Tuple

import bsp_tool

# import decompile_rbsp


bsp = bsp_tool.load_bsp("/data/ssd1/Mod/Titanfall2/maps/mp_angel_city.bsp")

geo_set_ranges = {
    (gc.first_geo_set, gc.num_geo_sets)
    for gc in bsp.CM_GRID_CELLS[:-len(bsp.MODELS)]
    if gc.num_geo_sets > 0}

indices = functools.reduce(
    lambda a, b: a | b, (
        {*range(start, start + length + 1)}
        for start, length in geo_set_ranges))

# prims = decompile_rbsp.geoset_primitives(bsp, indices)


def func_A(bsp, indices: Set[int]) -> Set[Tuple[int, int]]:
    """ignore straddle groups, ignore contents"""
    primitives = set()
    for i in indices:
        geo_set = bsp.CM_GEO_SETS[i]
        if geo_set.num_primitives == 1:
            type_ = geo_set.primitive.type
            index = geo_set.primitive.index
            primitives.add((type_, index))
        else:
            pstart = geo_set.primitive.index
            plength = geo_set.num_primitives
            pend = pstart + plength + 1
            primitives.update({
                (prim.type, prim.index)
                for prim in bsp.CM_PRIMITIVES[pstart:pend]})
    return primitives


def func_B(bsp, indices: Set[int]) -> Set[Tuple[int, int]]:
    """ignore straddle groups,  track contents"""
    primitives = set()
    for i in indices:
        geo_set = bsp.CM_GEO_SETS[i]
        if geo_set.num_primitives == 1:
            primitives.add(tuple(geo_set.primitive))
        else:
            pstart = geo_set.primitive.index
            plength = geo_set.num_primitives
            pend = pstart + plength + 1
            primitives.update({
                tuple(prim)
                for prim in bsp.CM_PRIMITIVES[pstart:pend]})
    return primitives


def func_C(bsp, indices: Set[int]) -> Set[Tuple[int, int]]:
    """ track straddle groups, ignore contents"""
    primitives = set()
    straddle_groups = set()
    for i in indices:
        geo_set = bsp.CM_GEO_SETS[i]
        if geo_set.straddle_group != 0:
            if geo_set.straddle_group in straddle_groups:
                continue
            straddle_groups.add(geo_set.straddle_group)
        if geo_set.num_primitives == 1:
            type_ = geo_set.primitive.type
            index = geo_set.primitive.index
            primitives.add((type_, index))
        else:
            pstart = geo_set.primitive.index
            plength = geo_set.num_primitives
            pend = pstart + plength + 1
            primitives.update({
                (prim.type, prim.index)
                for prim in bsp.CM_PRIMITIVES[pstart:pend]})
    return primitives


def func_D(bsp, indices: Set[int]) -> Set[Tuple[int, int]]:
    """ track straddle groups,  track contents"""
    primitives = set()
    straddle_groups = set()
    for i in indices:
        geo_set = bsp.CM_GEO_SETS[i]
        if geo_set.straddle_group != 0:
            if geo_set.straddle_group in straddle_groups:
                continue
            straddle_groups.add(geo_set.straddle_group)
        if geo_set.num_primitives == 1:
            primitives.add(tuple(geo_set.primitive))
        else:
            pstart = geo_set.primitive.index
            plength = geo_set.num_primitives
            pend = pstart + plength + 1
            primitives.update({
                tuple(prim)
                for prim in bsp.CM_PRIMITIVES[pstart:pend]})
    return primitives


# TODO: func_E, group prims by index first


def straddle_debug(bsp, indices: Set[int]):
    primitives = set()
    cheeky = collections.defaultdict(set)
    # ^ prims we miss if we skip
    freaky = {"single": 0, "groups": 0}
    straddle_groups = set()
    for i in indices:
        geo_set = bsp.CM_GEO_SETS[i]
        skip = False
        if geo_set.straddle_group != 0:
            skip = (geo_set.straddle_group in straddle_groups)
            straddle_groups.add(geo_set.straddle_group)
        if geo_set.num_primitives == 1:
            type_ = geo_set.primitive.type
            index = geo_set.primitive.index
            prim = (type_, index)
            if skip and prim not in primitives:
                freaky["single"] += 1
                cheeky[geo_set.straddle_group].add(prim)
            primitives.add(prim)
        else:
            pstart = geo_set.primitive.index
            plength = geo_set.num_primitives
            pend = pstart + plength + 1
            for raw_prim in bsp.CM_PRIMITIVES[pstart:pend]:
                prim = (raw_prim.type, raw_prim.index)
                if skip and prim not in primitives:
                    freaky["groups"] += 1
                    cheeky[geo_set.straddle_group].add(prim)
                primitives.add(prim)
    return primitives, cheeky, freaky, straddle_groups


if __name__ == "__main__":
    import time
    import timeit

    for func in (func_A, func_B, func_C, func_D)[::-1]:
        avg_time = timeit.timeit(lambda: func(bsp, indices), number=10)

        start_time = time.monotonic_ns()

        prims = func(bsp, indices)

        end_time = time.monotonic_ns()
        run_time = end_time - start_time

        print(
            f"{func.__name__} ({func.__doc__})",
            "found", len(prims), "primitives",
            f"in {run_time * (10 ** -9):.6f} seconds (average: {avg_time:.6f})")
