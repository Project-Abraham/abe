from abe.parse import common

import pytest


z_up_0 = common.Plane((0, 0, 1), 0)
planes = {
    "ints": ("(0 0 0) (0 1 0) (1 0 0)", z_up_0),
    "floats": ("(0.0 0.0 0.0) (0.0 1.0 0.0) (1.0 0.0 0.0)", z_up_0)}


@pytest.mark.parametrize(
    "raw_plane,expected", planes.values(), ids=planes.keys())
def test_from_string(raw_plane: str, expected: common.Plane):
    plane = common.Plane.from_string(raw_plane)
    assert plane == expected


# TODO: test_str (including fstr)
