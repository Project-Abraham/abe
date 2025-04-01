# https://quakewiki.org/wiki/Quake_Map_Format
import re

from ... import core
from ... import parser


class BrushSide(parser.Composite):
    # ( 0 0 0 ) ( 0 1 0 ) ( 0 0 1 ) material 0 0 0 1 1
    spec = {
        "plane": parser.composite.Plane,
        "shader": parser.basic.String,
        "s_offset": parser.basic.Float,
        "t_offset": parser.basic.Float,
        "rotation": parser.basic.Float,
        "s_scale": parser.basic.Float,
        "t_scale": parser.basic.Float}


class MapFile(core.MapFile):
    BrushSideClass = BrushSide

    @classmethod
    def from_file(cls, filepath: str):
        out = cls()
        node_depth = 0
        parse = {
            "Comment": parser.basic.Comment(),
            "KeyValuePair": parser.Composite.KeyValuePair(),  # TODO
            "BrushSide": cls.BrushSideClass()}
        with open(filepath) as source_file:
            for line_no, line in enumerate(source_file):
                line = line.strip()
                if line == "":
                    continue  # MRVN-Radiant .map can have empty lines
                elif parse["Comment"].describes(line):
                    out.comments[line_no] = parse["Comment"].parse(line)
                elif line.strip() == "{":
                    node_depth += 1
                    if node_depth == 1:
                        entity = core.Entity()
                        out.entities.append(entity)
                    elif node_depth == 2:
                        brush = core.Brush()
                        entity.brushes.append(brush)
                    else:
                        raise NotImplementedError()
                elif line.strip() == "}":
                    node_depth -= 1
                elif parse["KeyValuePair"].describes(line):
                    assert node_depth == 1, "keyvalues outside of entity"
                    key, value = parse["KeyValuePair"].parse(line)
                    entity[key] = value
                elif parse["BrushSide"].describes(line):
                    assert node_depth == 2, "brushside outside of brush"
                    brush.sides.append(parse["BrushSideClass"].parse(line))
                else:
                    raise RuntimeError(f"Couldn't parse line #{line_no}: '{line}'")
            assert node_depth == 0, f"{filepath} ends prematurely at line {line_no}"
        return out
