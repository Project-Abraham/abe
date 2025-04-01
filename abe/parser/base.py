from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple


class Basic:
    # subclass defined
    out_type: object
    pattern: str
    # generated
    regex: re.Pattern  # cached property

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.pattern!r} -> {self.out_type}>"

    def describes(self, string: str) -> bool:
        return self.regex.match(string) is not None

    @property
    def regex(self) -> re.Pattern:
        if not hasattr(self, "_regex"):
            self._regex = re.compile(self.pattern)
        return self._regex

    @classmethod
    def parse(cls, string: str) -> object:
        return cls.out_type(string)

    @classmethod
    def unparse(cls, object_: object) -> str:
        return str(object_)


def escape(string: str) -> str:
    special = ".?*+^$[](){}|\\"
    return "".join([(f"\\{c}" if c in special else c) for c in string])


class Composite:
    # NOTE: assumes all tokens are separated by a single space
    # -- this is a deeply flawed approach
    # -- use named regex groups instead: (?P<name>=...)
    # subclass defined
    out_type: object
    attr_parsers: List[Tuple[str, Basic | Composite | None]]
    # ^ [("attr", parser)]
    # generated
    pattern: str
    regex: re.Pattern  # w/ named groups & child patterns

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.pattern!r} -> {self.out_type}>"

    def describes(self, string: str) -> bool:
        return self.regex.match(string) is not None

    @property
    def pattern(self) -> str:
        if not hasattr(self, "_pattern"):
            self._pattern = " ".join([
                parser().pattern if parser is not None else escape(attr)
                for attr, parser in self.attr_parsers])
        return self._pattern

    @property
    def regex(self) -> re.Pattern:
        if not hasattr(self, "_regex"):
            self._regex = re.compile(self.pattern)
        return self._regex

    def dictify(self, string: str) -> Dict[str, Any]:
        return {
            attr: token
            for (attr, parser), token in zip(self.attr_parsers, string.split())
            if parser is not None}

    def parse(self, string: str) -> object:
        return self.out_type(**self.dictify(string))

    def unparse(self, object_: object) -> str:
        return " ".join([
            attr if parser is None else getattr(object_, attr)
            for attr, parser in self.attr_parsers])
