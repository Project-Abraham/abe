"""regex toolkit"""
from __future__ import annotations
import re
from typing import List

from ass import physics
from ass import vector


# uncompiled common snippets
comment = r"(\\\\|//).*"  # C++ style
double = r"([+-]?[0-9]+(\.[0-9]*)?(e[+-]?[0-9]+)?)"
# NOTE: 3 groups, 1st group encapsulates all
filepath = r"([A-Za-z0-9_\./\\:]+)"
integer = r"([+-]?[0-9]+)"
key_value_pair = r'"(.*)"\s"(.*)"'  # 2 groups
point = f"\\( ?{double} {double} {double} ?\\)"  # 9 groups
plane = f"{point} {point} {point}"  # 27 groups


def fstr(x: float) -> str:
    """str(float) without trailing zeroes"""
    x = round(x, 2)
    if x % 1.0 == 0.0:
        return str(int(x))
    return str(x)


class TokenClass:
    """helper class for text <-> object conversion"""
    pattern: re.Pattern  # compiled regex w/ groups

    def __str__(self) -> str:
        raise NotImplementedError()

    @classmethod
    def from_string(cls, string: str) -> TokenClass:
        match = cls.pattern.match(string)
        assert match is not None, f"{string=}, {cls.pattern=}"
        return cls.from_tokens(match.groups())

    @classmethod
    def from_tokens(cls, tokens: List[str]) -> TokenClass:
        raise NotImplementedError()


class Plane(physics.Plane, TokenClass):
    pattern = re.compile(plane)
    _triangle = None

    def __str__(self) -> str:
        if self._triangle is None:
            A, B, C = self.as_triangle()
        else:
            A, B, C = self._triangle
            # force use of the loaded values
            # to avoid accuracy drift on re-save
            # due to floating point rounding errors
        return " ".join(map(str, [Point(*A), Point(*B), Point(*C)]))

    @classmethod
    def from_tokens(cls, tokens: List[str]) -> Plane:
        Ax, Ay, Az, Bx, By, Bz, Cx, Cy, Cz = map(float, tokens[::3])
        A = vector.vec3(Ax, Ay, Az)
        B = vector.vec3(Bx, By, Bz)
        C = vector.vec3(Cx, Cy, Cz)
        out = cls.from_triangle(A, B, C)
        out._triangle = (A, B, C)  # preserved to minimise data loss
        return out


class Point(vector.vec3, TokenClass):
    pattern = re.compile(point)

    def __format__(self, format_spec: str = "") -> str:
        if format_spec == "":
            return str(self)
        else:
            x, y, z = [format(a, format_spec) for a in self]
            return f"({x} {y} {z})"

    def __str__(self):
        x, y, z = map(fstr, self)
        return f"({x} {y} {z})"

    @classmethod
    def from_tokens(cls, tokens: List[str]) -> Point:
        return cls(*map(float, tokens[::3]))
