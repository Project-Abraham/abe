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
        {*range(start, start + length)}
        for start, length in geo_set_ranges))

# prims = decompile_rbsp.geoset_primitives(bsp, indices)


# considering accuracy & clarity, this might be the best
def func_A(bsp, indices: Set[int]) -> Set[Tuple[int, int]]:
    """naive"""
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
            pend = pstart + plength
            primitives.update({
                (prim.type, prim.index)
                for prim in bsp.CM_PRIMITIVES[pstart:pend]})
    return primitives


# bit slower, but unique_contents could be useful later
def func_B(bsp, indices: Set[int]) -> Set[Tuple[int, int, int]]:
    """prim contents"""
    primitives = set()
    for i in indices:
        geo_set = bsp.CM_GEO_SETS[i]
        if geo_set.num_primitives == 1:
            primitives.add(tuple(geo_set.primitive))
        else:
            pstart = geo_set.primitive.index
            plength = geo_set.num_primitives
            pend = pstart + plength
            primitives.update({
                tuple(prim)
                for prim in bsp.CM_PRIMITIVES[pstart:pend]})
    return primitives


# fastest implementation by a lot! but also inaccurate
def func_C(bsp, indices: Set[int]) -> Set[Tuple[int, int]]:
    """straddle skip"""
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
            pend = pstart + plength
            primitives.update({
                (prim.type, prim.index)
                for prim in bsp.CM_PRIMITIVES[pstart:pend]})
    return primitives


# have to resort to tuples because types don't technically match
# MappedArray for GeoSet.Primitive vs. Primitive
# otherwise this could be a faster naive implementation
def func_D(bsp, indices: Set[int]) -> Set[Tuple[int, int, int]]:
    """paranoid"""
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
            pend = pstart + plength
            primitives.update({
                tuple(prim)
                for prim in bsp.CM_PRIMITIVES[pstart:pend]})
    return primitives


# still not good enough!
# some geo sets are split for seemingly arbitrary reasons
# same group, contents, primtype & brush side texture
# even contiguous geosets w/ contiguous primitive lists
# see: r2/mp_angel_city straddle_group[156]
def func_E(bsp, indices: Set[int]) -> Set[Tuple[int, int]]:
    """straddle skip fix"""
    primitives = set()
    seen = set()
    for i in indices:
        geo_set = bsp.CM_GEO_SETS[i]
        if geo_set.straddle_group != 0:
            skip_key = (
                geo_set.straddle_group,
                geo_set.primitive.unique_contents)
            if skip_key in seen:
                continue
            seen.add(skip_key)
        if geo_set.num_primitives == 1:
            type_ = geo_set.primitive.type
            index = geo_set.primitive.index
            primitives.add((type_, index))
        else:
            pstart = geo_set.primitive.index
            plength = geo_set.num_primitives
            pend = pstart + plength
            primitives.update({
                (prim.type, prim.index)
                for prim in bsp.CM_PRIMITIVES[pstart:pend]})
    return primitives


# in theory: accurate & fast
# in practice: the slowest by miles
# building the geosets set takes forever
def func_F(bsp, indices: Set[int]) -> Set[Tuple[int, int]]:
    """dedup geosets"""
    primitives = set()
    for geo_set in {bsp.CM_GEO_SETS[i] for i in indices}:
        # get primitive
        if geo_set.num_primitives == 1:  # inline prim
            type_ = geo_set.primitive.type
            index = geo_set.primitive.index
            primitives.add((type_, index))
        else:  # multiple primitives
            pstart = geo_set.primitive.index
            plength = geo_set.num_primitives
            pend = pstart + plength
            primitives.update({
                (prim.type, prim.index)
                for prim in bsp.CM_PRIMITIVES[pstart:pend]})
    return primitives


def straddle_debug(bsp, indices: Set[int]):
    """for inspecting invalid skips"""
    primitives = set()
    cheeky = collections.defaultdict(set)
    # ^ prims we miss if we skip
    freaky = {"single": 0, "groups": 0}
    seen = set()
    for i in indices:
        geo_set = bsp.CM_GEO_SETS[i]
        skip = False
        if geo_set.straddle_group != 0:
            skip_key = (
                geo_set.straddle_group,
                geo_set.primitive.unique_contents)
            skip = (skip_key in seen)
            seen.add(skip_key)
        if geo_set.num_primitives == 1:
            prim = tuple(geo_set.primitive)
            if skip and prim not in primitives:
                freaky["single"] += 1
                cheeky[geo_set.straddle_group].add(prim)
            primitives.add(prim)
        else:
            pstart = geo_set.primitive.index
            plength = geo_set.num_primitives
            pend = pstart + plength + 1
            for raw_prim in bsp.CM_PRIMITIVES[pstart:pend]:
                prim = tuple(raw_prim)
                if skip and prim not in primitives:
                    freaky["groups"] += 1
                    cheeky[geo_set.straddle_group].add(prim)
                primitives.add(prim)
    return primitives, cheeky, freaky, seen


if __name__ == "__main__":
    import time
    import timeit

    # TODO: precache bsp lumps
    # -- first run takes significantly longer
    # -- we need to A/B profile the initial bsp load
    # -- with & without precaching

    # profile funcs
    for func in (func_A, func_B, func_C, func_D, func_E, func_F):
        avg_time = timeit.timeit(lambda: func(bsp, indices), number=10)

        start_time = time.monotonic_ns()

        prims = func(bsp, indices)

        end_time = time.monotonic_ns()
        run_time = end_time - start_time

        print(
            f"{len(prims)} prims",
            f"{run_time * (10 ** -8):.3f}s",
            f"{avg_time:.3f}s average",
            f"{func.__name__} ({func.__doc__})",
            sep=" | ")
