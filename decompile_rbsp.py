# rebuild of bsp_tool.extensions.decompile_rbsp
import os
from typing import Dict, Set

import abe
import ass


# TODO:
# -- prop_static
# -- misc_model / Displacement (Tricoll)
# -- point entities (skipped for filesize reasons)

# NOTE:
# -- currently built for titanfall 2 maps
# -- getting brushes from CM_GRID is limiting us to clips
# -- hammer reports only clip, npcclip & blocklight textures


def decompile_brush(bsp, brush_index: int) -> abe.Brush:
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
        side.shader = bsp.TEXTURE_DATA_STRING_DATA[texdata.name_index].replace("\\", "/").lower()
        tv = bsp.CM_BRUSH_SIDE_TEXTURE_VECTORS[first_brush_side + i]
        side.texture_vector.s.axis = tv.s.axis
        side.texture_vector.t.axis = tv.t.axis
        side.texture_vector.s.offset = tv.s.offset
        side.texture_vector.t.offset = tv.t.offset
        abe_brush.sides[i] = side
    return abe_brush


# NOTE: built for titanfall2
def geosets_range_brush_indices(bsp, start: int, end: int) -> Set[int]:
    brush_indices = set()
    primitive_indices = set()
    for geo_set in bsp.CM_GEO_SETS[start:end]:
        if geo_set.num_primitives == 1:
            if geo_set.primitive.type == 0x00:
                brush_indices.add(geo_set.primitive.index)
        else:
            primitive_indices.update({
                geo_set.primitive.index + i
                for i in range(geo_set.num_primitives)})
    brush_indices.update({
        bsp.CM_PRIMITIVES[i].index
        for i in primitive_indices
        if bsp.CM_PRIMITIVES[i].type == 0x00})
    return brush_indices


# NOTE: sp_training only uses the first 448 of ~3K brushes
# -- turns out this is all clip brushes
# -- so where are the other brushes?
# -- are they also indexed by cm_grid?
# -- is this titanfall 2 specific?
def decompile_brush_entity(bsp, bsp_entity: Dict[str, str]) -> abe.Entity:
    abe_entity = abe.Entity(**bsp_entity)
    if abe_entity.classname == "worldspawn":
        # NOTE: this should get all the worldspawn geosets, but we'll see
        grid_cell = bsp.CM_GRID_CELLS[-len(bsp.MODELS)]
        start = 0
        end = grid_cell.first_geo_set + grid_cell.num_geo_sets
    elif abe_entity.get("model", "").startswith("*"):
        model_index = int(abe_entity.model[1:])
        grid_cell = bsp.CM_GRID_CELLS[-len(bsp.MODELS):][model_index]
        start = grid_cell.first_geo_set
        end = start + grid_cell.num_geo_sets
        del abe_entity["model"]
    else:
        raise RuntimeError("not a brush entity!")
    brush_indices = geosets_range_brush_indices(bsp, start, end)
    if len(brush_indices) > 0:
        print(f"{min(brush_indices)=}, {max(brush_indices)=}")
    abe_entity.brushes = [
        decompile_brush(bsp, i)
        for i in sorted(brush_indices)]
    return abe_entity


def decompile_map(bsp) -> abe.MapFile:
    base_filename = os.path.splitext(bsp.filename)[0]
    out = abe.MapFile(f"{base_filename}.map")

    bsp_worldspawn = bsp.ENTITIES[0]
    assert bsp_worldspawn.get("classname", "") == "worldspawn"
    abe_worldspawn = decompile_brush_entity(bsp, bsp_worldspawn)
    out.entities.append(abe_worldspawn)

    # NOTE: currently only brush entities
    # -- skipping point entities to save on filesize

    # *.0000.bsp_lump brush entities
    out.entities.extend([
        decompile_brush_entity(bsp, bsp_entity)
        for bsp_entity in bsp.ENTITIES
        if bsp_entity.get("model", "").startswith("*")])

    # *.ent brush entities
    for ent_file in ("env", "fx", "script", "snd", "spawn"):
        out.entities.extend([
            decompile_brush_entity(bsp, bsp_entity)
            for bsp_entity in getattr(bsp, f"ENTITIES_{ent_file}")
            if bsp_entity.get("model", "").startswith("*")])

    return out
