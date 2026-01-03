from __future__ import annotations
import re
from typing import Dict, List

from ... import texture
from ... import base
from .. import common
from . import map220

import breki


# TODO: Entity connections (Entity IO)
# TODO: validate "id" for Entity, Brush & BrushSide
# TODO: Displacements
# TODO: `hidden` nodes
# TODO: visgroup filtering to find ents etc.


class Node:
    node_type: str
    key_values: List[(str, str)]
    # NOTE: like a dict, but keys can appear more than once
    # -- add new entries w/ .append((key, value)) [.extend is also valid]
    # -- dict(key_values) will use the last occurence of each key
    nodes: List[Node]

    def __init__(self, node_type: str):
        self.node_type = node_type
        self.key_values = list()
        self.nodes = list()

    def __delitem__(self, key: str):
        index = self.key_values.index((key, self[key]))
        self.key_values.pop(index)

    def __getitem__(self, key: str) -> str:
        return dict(self.key_values)[key]

    def __repr__(self) -> str:
        return "\n".join([
            self.node_type,
            "{",
            *[f'\t"{k}" "{v}"' for k, v in self.key_values],
            *[
                f"\t... hid {len(nodes)} {type_} nodes ..."
                for type_, nodes in self.nodes_by_type().items()],
            "}"])

    def __setitem__(self, key: str, value: str):
        index = self.key_values.index((key, self[key]))
        self.key_values[index] = (key, value)

    def __str__(self) -> str:
        # NOTE: key values are not sanitised
        # -- double quotes & curly braces will break
        # NOTE: child nodes will not be indented
        return "\n".join([
            self.node_type,
            "{",
            *[
                f'\t"{key}" "{value}"'
                for key, value in self.key_values],
            *map(str, self.nodes),
            "}"])

    # KEY VALUE HANDLERS

    def get(self, key: str, default=None) -> str:
        return dict(self.key_values).get(key, default)

    def get_all(self, key: str) -> List[str]:
        return [
            entry_value
            for entry_key, entry_value in self.key_values
            if entry_key == key]

    def items(self) -> List[(str, str)]:
        return self.key_values

    def keys(self) -> List[str]:
        return [key for key, value in self.key_values]

    def update(self, kv_dict: Dict[str, str]):
        for key, value in kv_dict.items():
            self.key_values[key] = value

    def values(self) -> List[str]:
        return [value for key, value in self.key_values]

    # CHILD NODE HANDLERS

    def nodes_by_type(self) -> Dict[str, List[Node]]:
        return {
            type_: [
                node
                for node in self.nodes
                if node.node_type == type_]
            for type_ in sorted(set(
                node.node_type
                for node in self.nodes))}


# TODO: class DispInfo(generic.DispInfo):


class BrushSide(base.BrushSide):
    def as_node(self) -> Node:
        out = Node("side")
        key_values = {
            "plane": common.Plane(*self.plane.as_triangle()),
            "material": self.shader,
            **{f"{axis}axis": projection
               for axis, projection in zip("uv", self.texture_vector)},
            "rotation": self.texture_rotation}
        out.update({
            key: str(value)
            for key, value in key_values.items()})
        # TODO: dispinfo child node
        return out

    @classmethod
    def from_node(cls, node: Node) -> BrushSide:
        assert node.node_type == "side"
        plane = common.Plane.from_string(node["plane"])
        shader = node["material"]
        uaxis, vaxis = [
            map220.ProjectionAxis.from_string(node[f"{axis}axis"])
            for axis in "uv"]
        texture_vector = texture.TextureVector(uaxis, vaxis)
        rotation = node["rotation"]
        # TODO: node.nodes_by_type().get("dispinfo", [])
        return cls(plane, shader, texture_vector, rotation)


class Brush(base.Brush):
    def as_node(self) -> Node:
        out = Node("solid")
        out.nodes = [side.as_node() for side in self.sides]
        # NOTE: no editor node or entities
        return out

    @classmethod
    def from_node(cls, node: Node) -> Brush:
        assert node.node_type == "solid"
        return cls([
            BrushSide.from_node(node)
            for node in node.nodes_by_type().get("side", [])])


class Entity(base.Entity):
    # TODO: Connections (Entity IO)

    def as_node(self) -> Node:
        out = Node("entity")
        out.key_values = [(k, self[k]) for k in self._keys]
        out.nodes = [b.as_node() for b in self.brushes]
        return out

    @classmethod
    def from_node(cls, node: Node) -> Entity:
        assert node.node_type in ("entity", "world")
        out = cls(**dict(node.key_values))
        out.brushes = [
            Brush.from_node(node)
            for node in node.nodes_by_type().get("solid", [])]
        return out


class Vmf(base.MapFile, breki.TextFile):
    exts = ["*.vmf"]
    nodes: List[Node]

    def __init__(self, filepath: str, archive=None, code_page=None):
        super().__init__(filepath, archive, code_page)
        self.nodes = list()

    def as_lines(self) -> List[str]:
        # TODO: try to match valve's node order:
        # -- ???, world, entities, cameras, cordons
        # TODO: entities & brushes -> nodes -> str
        raise NotImplementedError()

    def nodes_by_type(self) -> Dict[str, List[Node]]:
        return {
            type_: [
                node
                for node in self.nodes
                if node.node_type == type_]
            for type_ in sorted(set(
                node.node_type
                for node in self.nodes))}

    def parse(self):
        if self.is_parsed:
            return
        self.is_parsed = True
        # regex patters
        patterns = {
            "KeyValuePair": re.compile(common.key_value_pair),
            "NodeType": re.compile(r"[a-z_]+")}

        def parent() -> Node:
            parent_node = self
            for i in range(node_depth):
                parent_node = parent_node.nodes[-1]
            return parent_node

        # parse lines
        node_depth = 0
        node_type = None
        for line_no, line in enumerate(self.stream):
            line = line.strip()  # ignore indentation & trailing newline
            # TODO: assert each open curly brace is preceded by a nodetype
            if patterns["NodeType"].match(line) is not None:
                node_type = line
            elif line == "{":
                node = Node(node_type)
                parent().nodes.append(node)
                node_depth += 1
            elif patterns["KeyValuePair"].match(line) is not None:
                key, value = patterns["KeyValuePair"].match(line).groups()
                node.key_values.append((key, value))
            elif line == "}":
                node_depth -= 1
                node = parent()
            else:
                raise RuntimeError(f"Couldn't parse line #{line_no}: '{line}'")
        assert node_depth == 0

        # nodes -> entities
        nodes_dict = self.nodes_by_type()
        assert len(nodes_dict["world"]) == 1
        self.entities = [
            Entity.from_node(node)
            for node in [
                nodes_dict["world"][0],
                *nodes_dict.get("entity", [])]]
        # self.nodes = [
        #     node
        #     for node in out.nodes
        #     if node.node_type not in ("world", "entity")]
