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
point = f"\\( {double} {double} {double} \\)"  # 9 groups
plane = f"{point} {point} {point}"  # 27 groups


class TokenClass:
    """helper class for text <-> object conversion"""
    pattern: re.Pattern  # compiled regex w/ groups

    def __str__(self) -> str:
        raise NotImplementedError()

    @classmethod
    def from_string(cls, string: str) -> TokenClass:
        match = cls.pattern.match(string)
        assert match is not None
        return cls.from_tokens(match.groups())

    @classmethod
    def from_tokens(cls, tokens: List[str]) -> TokenClass:
        raise NotImplementedError()


class Plane(physics.Plane, TokenClass):
    pattern = re.compile(plane)
    _triangle = None

    def __str__(self) -> str:
        A, B, C = self.as_triangle() if self._triangle is None else self._triangle
        # NOTE: self._triangle will override any changes
        # -- self._triangle should be more accurate
        return " ".join(["(", *A, ")", "(", *B, ")", "(", *C, ")"])

    @classmethod
    def from_tokens(cls, tokens: List[str]) -> Plane:
        Ax, Ay, Az, Bx, By, Bz, Cx, Cy, Cz = map(float, tokens[::3])
        A = vector.vec3(Ax, Ay, Az)
        B = vector.vec3(Bx, By, Bz)
        C = vector.vec3(Cx, Cy, Cz)
        out = cls.from_triangle(A, B, C)
        out._triangle = (A, B, C)  # preserved to minimise data loss
        return out
