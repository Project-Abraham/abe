from abe.parse import common

import pytest


points = {
    "ints": ("(0 1 2)", common.Point(0, 1, 2)),
    "floats": ("(-3 +4.5 6e+7)", common.Point(-3, 4.5, 6e7))
}


@pytest.mark.parametrize(
    "raw_point,expected", points.values(), ids=points.keys())
def test_from_string(raw_point: str, expected: common.Point):
    point = common.Point.from_string(raw_point)
    assert point == expected


# TODO: test_str (including fstr)
# TODO: test_format
