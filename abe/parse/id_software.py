# https://quakewiki.org/wiki/Quake_Map_Format
from __future__ import annotations
import re
from typing import List

from .. import texture
from .. import base
from . import common

import breki


class BrushSide(base.BrushSide, common.TokenClass):
    pattern = re.compile(" ".join([
        common.plane, common.filepath, *(common.double,)*5]))

    def __str__(self) -> str:
        return " ".join(map(str, [
            self.plane,
            self.shader,
            self.texture_vector.s.offset,
            self.texture_vector.t.offset,
            self.texture_rotation,
            self.texture_vector.s.scale,
            self.texture_vector.t.scale]))

    @classmethod
    def from_tokens(cls, tokens: List[str]) -> BrushSide:
        plane = common.Plane.from_tokens(tokens[:27])
        shader = tokens[27]
        s_offset, t_offset, rotation, s_scale, t_scale = map(float, tokens[28::3])
        texture_vector = texture.TextureVector.from_normal(plane.normal)
        texture_vector.s.offset = s_offset
        texture_vector.t.offset = t_offset
        texture_vector.s.scale = s_scale
        texture_vector.t.scale = t_scale
        return cls(plane, shader, texture_vector, rotation)


class QuakeMap(base.MapFile, breki.TextFile):
    exts = ["*.map"]
    BrushSideClass = BrushSide

    def parse(self):
        if self.is_parsed:
            return
        self.is_parsed = True
        # regex patterns
        patterns = {
            "BrushSide": self.BrushSideClass.pattern,
            "Comment": re.compile(common.comment),
            "KeyValuePair": re.compile(common.key_value_pair)}
        # parse lines
        node_depth = 0
        for line_no, line in enumerate(self.stream):
            line = line.strip()
            if line == "":
                continue  # MRVN-Radiant
            elif patterns["Comment"].match(line) is not None:
                # NOTE: only catches full line comments
                # TODO: catch trailing comments
                self.comments[line_no] = line
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
                brush.sides.append(self.BrushSideClass.from_string(line))
            else:
                raise RuntimeError(f"Couldn't parse line #{line_no}: '{line}'")
        assert node_depth == 0, f"file ends prematurely at line {line_no}"
