import re

from abe.parse import common

import pytest


double = {
    "unsigned int": ("0", None, None),
    "signed int": ("+1", None, None),
    "unsigned decimal": ("2.34", ".34", None),
    "signed decimal": ("-5.67", ".67", None),
    "unsigned exponent": ("8e9", None, "e9"),
    "signed exponent": ("+1e-10", None, "e-10"),
    "unsigned exponent w/ decimal": ("2.34e5", ".34", "e5"),
    "signed exponent w/ decial": ("-6.78e+9", ".78", "e+9")}


@pytest.mark.parametrize(
    "base,decimal,exponent", double.values(), ids=double.keys())
def test_double(base: str, decimal: str, exponent: str):
    pattern = re.compile(common.double)
    match = pattern.match(base)
    assert match is not None
    expected = (base, decimal, exponent)
    assert match.groups() == expected
