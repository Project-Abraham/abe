from . import base
from . import basic

from .. import physics
from .. import vector


class Point(base.Composite):
    out_type = vector.vec3
    attr_parsers = [
        ("(", None),
        ("x", basic.Float),
        ("y", basic.Float),
        ("z", basic.Float),
        (")", None)]


class Plane(base.Composite):
    out_type = physics.Plane
    attr_parsers = [
        ("A", Point),
        ("B", Point),
        ("C", Point)]

    def parse(self, string: str) -> physics.Plane:
        return physics.Plane.from_triangle(**self.dictify(string))

    def unparse(self, plane: physics.Plane) -> str:
        triangle = plane.as_triangle()
        return " ".join(Point.unparse(p) for p in triangle)
