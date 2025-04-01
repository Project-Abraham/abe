from . import base


class Comment(base.Basic):
    out_type = str
    pattern = r"// .*"

    def parse(self, comment: str) -> str:
        return comment.partition(" ")[2]

    def unparse(self, comment: str) -> str:
        return f"// {comment}"


class Float(base.Basic):
    out_type = float
    pattern = r"[+-]?[0-9]+(\.[0-9]+(e[+-]?[0-9]+)?)?"


class Integer(base.Basic):
    out_type = int
    pattern = r"[+-]?[0-9]+"


class String(base.Basic):
    out_type = str
    pattern = r"[^ ]+"
