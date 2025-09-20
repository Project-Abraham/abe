# https://quakewiki.org/wiki/Quake_Map_Format#Valve_variation_of_the_format
from __future__ import annotations
import re
from typing import List

from ... import texture
from ... import base
from .. import common
from .. import id_software


class ProjectionAxis(texture.ProjectionAxis, common.TokenClass):
    pattern = re.compile(" ".join([
        r"\[", *(common.double,)*4, r"\]"]))

    def __str__(self) -> str:
        return " ".join(map(str, ["[", *self.axis, self.offset, "]"]))

    @classmethod
    def from_tokens(cls, tokens: List[str]) -> ProjectionAxis:
        x, y, z, offset = map(float, tokens[::3])
        return cls((x, y, z), offset)


class BrushSide(base.BrushSide, common.TokenClass):
    pattern = re.compile(" ".join([
        common.plane, common.filepath,
        *(r"\[", *(common.double,)*4, r"\]",)*2,
        *(common.double,)*3]))

    def __str__(self) -> str:
        return " ".join(map(str, [
            self.plane, self.shader,
            self.texture_vector.s,
            self.texture_vector.t,
            self.rotation,
            self.texture_vector.s.scale,
            self.texture_vector.t.scale]))

    @classmethod
    def from_tokens(cls, tokens: List[str]) -> BrushSide:
        plane = common.Plane.from_tokens(tokens[:27])
        shader = tokens[27]
        s_axis = ProjectionAxis.from_tokens(tokens[28:][:12])
        t_axis = ProjectionAxis.from_tokens(tokens[40:][:12])
        rotation = float(tokens[52])
        s_axis.scale, t_axis.scale = map(float, tokens[55::3])
        texture_vector = texture.TextureVector(s_axis, t_axis)
        return cls(plane, shader, texture_vector, rotation)


class Valve220Map(id_software.QuakeMap):
    BrushSideClass = BrushSide
