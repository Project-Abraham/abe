# https://wiki.zeroy.com/index.php?title=Call_of_duty_4:_.MAP_file_structure
# NOTE: might need to use Wayback Machine (web.archive.org)
from __future__ import annotations
import re
from typing import List

from .. import texture
from .. import base
from . import common

from ass import vector
import breki


# TODO: Curves & other non-brush geo

class Projection(common.TokenClass):
    width: int
    height: int
    unknown: List[float]  # x_offset, y_offset, rotation, unknown?
    # values observed in unknown[:2] feel like pixel counts (512, 768 etc.)
    # observed 0, 180 & -180 for unknown[2]
    # observed 0 for unknown[3]; need more samples
    pattern = re.compile(" ".join([
        *(common.integer,)*2, *(common.double,)*4]))

    def __init__(self, width, height, *unknown):
        self.width = width
        self.height = height
        self.unknown = unknown

    def __repr__(self) -> str:
        args = ", ".join(map(str, [self.width, self.height, *self.unknown]))
        return f"{self.__class__.__name__}({args})"

    def __eq__(self, other: Projection) -> bool:
        return hash(self) == hash(other)

    def __hash__(self):
        return hash((self.width, self.height, *self.unknown))

    def __str__(self) -> str:
        return " ".join(map(str, [self.width, self.height, *self.unknown]))

    def as_texture_vector(self) -> texture.TextureVector:
        raise NotImplementedError()

    def uv_at(self, point: vector.vec3) -> vector.vec2:
        raise NotImplementedError()

    @classmethod
    def from_texture_vector(cls, texture_vector) -> Projection:
        raise NotImplementedError()

    @classmethod
    def from_tokens(cls, tokens: List[str]) -> Projection:
        width, height = map(int, tokens[:2])
        unknown = map(float, tokens[2::3])
        return cls(width, height, *unknown)


class BrushSide(base.BrushSide, common.TokenClass):
    pattern = re.compile(" ".join([
        common.plane, common.filepath,
        *(common.integer,)*2, *(common.double,)*4,  # shader projection
        common.filepath,
        *(common.integer,)*2, *(common.double,)*4]))  # lightmap projection

    def __str__(self) -> str:
        return " ".join(map(str, [
            self.plane,
            self.shader, self.shader_projection,
            self.lightmap, self.lightmap_projection]))

    @classmethod
    def from_tokens(cls, tokens: List[str]) -> BrushSide:
        plane = common.Plane.from_tokens(tokens[:27])
        shader = tokens[27]
        shader_projection = Projection.from_tokens(tokens[28:][:14])
        lightmap = tokens[42]
        lightmap_projection = Projection.from_tokens(tokens[43:][:14])
        out = cls(plane, shader)
        out.lightmap = lightmap
        out.shader_projection = shader_projection
        out.lightmap_projection = lightmap_projection
        out.texture_vector = None
        # out.texture_vector = property(
        #     lambda s: s.shader_projection.as_texture_vector())
        return out


class CoD4Map(base.MapFile, breki.TextFile):
    exts = ["*.map"]

    def parse(self):
        if self.is_parsed:
            return
        self.is_parsed = True
        # regex patterns
        patterns = {
            "BrushSide": BrushSide.pattern,
            "Comment": re.compile(common.comment),
            "KeyValuePair": re.compile(common.key_value_pair),
            "Flags": re.compile(r'"[A-Za-z0-9_ ]+"\s+flags(\s+active)?')}
        # parse lines
        node_depth = 0
        assert self.stream.readline().rstrip() == "iwmap 4"
        for line_no, line in enumerate(self.stream):
            line = line.strip()
            if patterns["Comment"].match(line) is not None:
                # NOTE: only catches full line comments
                # TODO: catch trailing comments
                self.comments[line_no] = line
            elif patterns["Flags"].match(line) is not None:
                pass  # ignore
            elif line.strip() == "{":
                node_depth += 1
                if node_depth == 1:
                    entity = base.Entity()
                    self.entities.append(entity)
                elif node_depth == 2:
                    brush = base.Brush()
                    entity.brushes.append(brush)
                else:
                    raise NotImplementedError()
            elif line.strip() == "}":
                node_depth -= 1
            elif patterns["KeyValuePair"].match(line) is not None:
                assert node_depth == 1, "keyvalues outside of entity"
                key, value = patterns["KeyValuePair"].match(line).groups()
                entity[key] = value
            elif patterns["BrushSide"].match(line) is not None:
                assert node_depth == 2, "brushside outside of brush"
                brush.sides.append(BrushSide.from_string(line))
            else:
                raise RuntimeError(f"Couldn't parse line #{line_no}: '{line}'")
        assert node_depth == 0, f"stream ends prematurely at line {line_no}"
