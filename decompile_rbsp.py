# rebuild of bsp_tool.extensions.decompile_rbsp
import collections
import functools
import os
import re
from typing import Dict, List, Set, Tuple

import abe
import ass

from bsp_tool.respawn import RespawnBsp as Bsp
from bsp_tool.branches.respawn import titanfall2 as r2


# TODO:
# -- [ ] prop_static
# -- [X] misc_tricoll
# -- [X] point entities (skipping all except spawnpoints)

# NOTE: currently built for titanfall 2 maps


Entity = Dict[str, str]  # Bsp entity type


# NOTE: need to process starcoll for apex legends triggers
def decompile_trigger(trigger: Entity) -> abe.Entity:
    # TODO: discard bevel planes (sqrt2 x/y & bounds corners)
    # map bounds
    mins_str = trigger["*trigger_bounds_mins"]
    mins = ass.vector.vec3(*map(float, mins_str.split(" ")))
    maxs_str = trigger["*trigger_bounds_maxs"]
    maxs = ass.vector.vec3(*map(float, maxs_str.split(" ")))
    bounds = ass.physics.AABB.from_mins_maxs(mins, maxs)
    # collect planes
    pattern = re.compile(r"\*trigger_brush_([0-9]+)_plane_([0-9]+)")
    brush_planes = collections.defaultdict(dict)
    for key, value in trigger.items():
        match = pattern.match(key)
        if match is not None:
            brush_index = int(match.group(1))
            plane_index = int(match.group(2))
            a, b, c, d = map(float, value.split(" "))
            plane = ass.physics.Plane(ass.vector.vec3(a, b, c), d)
            if not plane.is_bevel_of(bounds):
                brush_planes[brush_index][plane_index] = plane
    # build entity
    out = abe.Entity(**{
        key: value
        for key, value in trigger.items()
        if not key.startswith("*trigger_")})
    # TODO: classname/editorclass lookup table for shader
    # TODO: BrushSide texture_vectors aren't calculated per-side
    out.brushes = [
        abe.Brush([
            abe.BrushSide(plane, shader="tools/toolstrigger")
            for plane in planes.values()])
        for brush_index, planes in brush_planes.items()]
    return out


def decompile_brush(bsp: Bsp, brush_index: int) -> abe.Brush:
    bsp_brush = bsp.CM_BRUSHES[brush_index]
    # BrushSide Planes
    bounds = ass.physics.AABB.from_origin_extents(
        bsp_brush.origin, bsp_brush.extents)
    abe_brush = abe.Brush.from_bounds(bounds)
    for i in range(bsp_brush.num_plane_offsets):
        offset = bsp_brush.brush_side_offset + i
        brush_plane_offset = offset - bsp.CM_BRUSH_SIDE_PLANE_OFFSETS[offset]
        plane_index = bsp.CM_GRID.first_brush_plane + brush_plane_offset
        normal, distance = bsp.PLANES[plane_index]
        plane = ass.physics.Plane(normal, distance)
        abe_brush.sides.append(abe.BrushSide(plane))
    first_brush_side = bsp_brush.index * 6 + bsp_brush.brush_side_offset
    # BrushSide shaders & TextureVectors
    for i, side in enumerate(abe_brush.sides):
        properties = bsp.CM_BRUSH_SIDE_PROPERTIES[i + first_brush_side]
        texdata = bsp.TEXTURE_DATA[properties.texture_data]
        texture_path = bsp.TEXTURE_DATA_STRING_DATA[texdata.name_index]
        side.shader = texture_path.replace("\\", "/").lower()
        tv = bsp.CM_BRUSH_SIDE_TEXTURE_VECTORS[first_brush_side + i]
        side.texture_vector.s.axis = tv.s.axis
        side.texture_vector.t.axis = tv.t.axis
        side.texture_vector.s.offset = tv.s.offset
        side.texture_vector.t.offset = tv.t.offset
        abe_brush.sides[i] = side
    return abe_brush


def geoset_primitives(bsp: Bsp, indices: Set[int]) -> Set[Tuple[int, int]]:
    primitives = set()
    for i in indices:
        geo_set = bsp.CM_GEO_SETS[i]
        # get primitive
        if geo_set.num_primitives == 1:  # inline prim
            type_ = geo_set.primitive.type
            index = geo_set.primitive.index
            primitives.add((type_, index))
        else:  # multiple primitives
            start = geo_set.primitive.index
            length = geo_set.num_primitives
            end = start + length
            primitives.update({
                (prim.type, prim.index)
                for prim in bsp.CM_PRIMITIVES[start:end]})
    return primitives


def decompile_solid_entity(bsp: Bsp, bsp_entity: Entity) -> List[abe.Entity]:
    abe_entity = abe.Entity(**bsp_entity)
    # get GridCell indices
    if abe_entity.classname == "worldspawn":
        grid_cells = bsp.CM_GRID_CELLS[:-len(bsp.MODELS)]
        grid_cells.append(bsp.CM_GRID_CELLS[-len(bsp.MODELS)])
        # TODO: what's the difference between these two?
        # eliminate duplicate indices
        spans = {
            (gc.first_geo_set, gc.num_geo_sets)
            for gc in grid_cells}
        indices = functools.reduce(
                lambda a, b: a | b, (
                    {*range(start, start + length)}
                    for start, length in spans))
        model_index = 0  # keep for status report
    elif abe_entity.get("model", "").startswith("*"):
        model_index = int(abe_entity.model[1:])
        grid_cell = bsp.CM_GRID_CELLS[-len(bsp.MODELS):][model_index]
        start = grid_cell.first_geo_set
        length = grid_cell.num_geo_sets
        indices = [*range(start, start + length)]
        del abe_entity["model"]  # solid ents can't have "model" keyval
    else:
        ent_id = f"{bsp_entity['classname']}"
        # TODO: editorclass / targetname / link_guid / script_ref
        raise RuntimeError(f"{ent_id} is not a solid entity!")
    # get geometry
    # TODO: break off tricoll & prop stages
    # -- will be optional, for perf reasons
    tricolls = list()
    primitives = geoset_primitives(bsp, indices)  # keep for status report
    # early status report
    ent_id = f"{bsp_entity['classname']}"
    # TODO: targetname / link_guid / script_ref
    type_s = [type_ for type_, index in primitives]
    census = {type_.name: type_s.count(type_) for type_ in set(type_s)}
    print(f"{model_index: 3d} {ent_id} {census}")
    for type_, index in primitives:
        if type_ == r2.PrimitiveType.BRUSH:
            abe_entity.brushes.append(decompile_brush(bsp, index))
        elif type_ == r2.PrimitiveType.TRICOLL:
            # TODO: group by straddle_group
            # tricoll[f"tricoll-{index:06d}"] = bsp.tricoll_model(index)
            tricolls.append(index)
        elif type_ == r2.PrimitiveType.PROP:
            ...  # TODO: more point entities
    # export tricoll (TODO: separate func)
    if len(tricolls) > 0:
        scene_filepath = f"tricoll/{bsp.filename[:-4]}/{model_index:03d}.obj"
        scene = ass.scene.wavefront.Obj.from_models(
            scene_filepath, {
                f"tricoll-{index:06d}": bsp.tricoll_model(index)
                for index in tricolls})
        models_dir = "/".join([  # HACK
            "/data/ssd1/Mod/_tools/Source Engine - Respawn",
            "MRVN-Radiant_games/Titanfall2/models"])
        scene.save_as("/".join([models_dir, scene_filepath]))
        print(f"+ {scene_filepath} ({len(tricolls)})")
        # TODO: set abe_entity as parent
        # TODO: recalc origin & angles to match abe_entity
        tricoll_entity = abe.Entity(
            classname="misc_tricoll",
            origin="0 0 0",
            angles="0 0 -90",  # HACK
            model=f"models/{scene_filepath}")
        return (abe_entity, tricoll_entity)
    return (abe_entity,)


def decompile_map(bsp) -> abe.MapFile:
    base_filename = os.path.splitext(bsp.filename)[0]
    out = abe.MapFile(f"{base_filename}.map")

    def is_solid(ent: Entity) -> bool:
        return any([
            bsp_entity["classname"] == "worldspawn",
            bsp_entity.get("model", "").startswith("*")])

    def is_trigger(ent: Entity) -> bool:
        # TEST: would a classname check be faster?
        return any(key.startswith("*trigger_") for key in ent)

    # TODO: use bsp.ENTITY_PARTITIONS
    partitions = ("env", "fx", "script", "snd", "spawn")  # .ent
    entity_blocks = (
        "ENTITIES",  # .0000.bsp_lump
        *(f"ENTITIES_{block}" for block in partitions))
    for block_name in entity_blocks:
        for i, bsp_entity in enumerate(getattr(bsp, block_name)):
            if is_solid(bsp_entity):
                out.entities.extend(decompile_solid_entity(bsp, bsp_entity))
            elif is_trigger(bsp_entity):
                out.entities.append(decompile_trigger(bsp_entity))
            elif block_name == "ENTITIES_spawn":  # spawnpoints
                out.entities.append(abe.Entity(**bsp_entity))
            else:
                pass  # skip to reduce clutter

    assert len(out.entities) >= 1
    assert out.entities[0]["classname"] == "worldspawn"

    return out
