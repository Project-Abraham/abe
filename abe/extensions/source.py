from typing import List

from .. import geometry
from .. import vector


class Displacement:
    power: int
    top_left: vector.vec3
    vectors: List[vector.vec3]

    def as_mesh(base_quad: geometry.Polygon) -> geometry.Mesh:
        assert len(base_quad.vertices) == 4, "not a quad"
        raise NotImplementedError()
