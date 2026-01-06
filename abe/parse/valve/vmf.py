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


class BrushSide(base.BrushSide):
    def as_node(self) -> Node:
        out = Node("side")
        out.update({
            "plane": common.Plane.from_triangle(*self.plane.as_triangle()),
            "material": self.shader,
            **{f"{axis}axis": ProjectionAxis(*projection)
               for axis, projection in zip("uv", self.texture_vector)},
            "rotation": self.texture_rotation})
        # TODO: dispinfo child node
        return out

    @classmethod
    def from_node(cls, node: Node) -> BrushSide:
        assert node.node_type == "side"
        plane = common.Plane.from_string(node["plane"])
        shader = node["material"]
        uaxis, vaxis = [
            ProjectionAxis.from_string(node[f"{axis}axis"])
            for axis in "uv"]
        texture_vector = texture.TextureVector(uaxis, vaxis)
        rotation = node["rotation"]
        # TODO: node.nodes_by_type().get("dispinfo", [])
        return cls(plane, shader, texture_vector, rotation)


class Brush(base.Brush):
    def as_node(self) -> Node:
        out = Node("solid")
        out.nodes = [
            BrushSide.as_node(side)
            for side in self.sides]
        # NOTE: no editor or group nodes
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
        out.key_values = [(key, self[key]) for key in self._keys]
        out.nodes = [
            Brush.as_node(brush)
            for brush in self.brushes]
        return out

    @classmethod
    def from_node(cls, node: Node) -> Entity:
        assert node.node_type in ("entity", "world")
        out = cls(**dict(node.key_values))
        out.brushes = [
            Brush.from_node(node)
            for node in node.nodes_by_type().get("solid", [])]
        return out


# TODO: class DispInfo(base.DispInfo):


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
        try:  # override
            index = self.key_values.index((key, self[key]))
            self.key_values[index] = (key, value)
        except KeyError:
            self.key_values.append((key, value))

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
            self[key] = value

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


class ProjectionAxis(map220.ProjectionAxis):
    pattern = re.compile("".join([
        r"\[ ?", " ".join([common.double] * 4), r" ?\] ", common.double]))

    def __init__(self, axis, offset=None, scale=None):
        scale = 0.25 if scale is None else scale
        super().__init__(axis, offset, scale)

    def __str__(self) -> str:
        axis = [common.fstr(a) for a in self.axis]
        offset = common.fstr(self.offset)
        scale = common.fstr(self.scale)
        return " ".join(["[", *axis, offset, "]", scale])

    @classmethod
    def from_tokens(cls, tokens: List[str]) -> ProjectionAxis:
        x, y, z, offset, scale = map(float, tokens[::3])
        return cls((x, y, z), offset, scale)


class Vmf(base.MapFile, breki.TextFile):
    exts = ["*.vmf"]
    nodes: List[Node]

    def __init__(self, filepath: str, archive=None, code_page=None):
        super().__init__(filepath, archive, code_page)
        self.nodes = list()

    def as_lines(self) -> List[str]:
        self.rebuild_nodes()
        return list(map(str, self.nodes))

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

    def rebuild_nodes(self):
        new_nodes = list()
        nodes_dict = self.nodes_by_type()

        if "versioninfo" in nodes_dict:
            assert len(nodes_dict["versioninfo"]) == 1
            version_info = nodes_dict["versioninfo"][0]
        else:
            version_info = Node("versioninfo")
            version_info.update({
                "editorversion": 400,
                "formatversion": 100,
                "mapversion": 1,
                "prefab": 0})
        new_nodes.append(version_info)

        if "visgroups" in nodes_dict:
            assert len(nodes_dict["visgroups"]) == 1
            visgroups = nodes_dict["visgroups"][0]
        else:
            visgroups = Node("visgroups")
        new_nodes.append(visgroups)

        if "viewsettings" in nodes_dict:
            assert len(nodes_dict["viewsettings"]) == 1
            view_settings = nodes_dict["viewsettings"][0]
        else:
            view_settings = Node("viewsettings")
            view_settings.update({
                "bShow3DGrid": 0,
                "bShowGrid": 1,
                "bShowLogicalGrid": 0,
                "bSnapToGrid": 1,
                "nGridSpacing": 16})
        new_nodes.append(view_settings)

        if len(self.entities) != 0:
            worldspawn = self.entities[0]
        else:  # empty world
            worldspawn = Entity()

        world_settings = {
            "id": 1,
            "mapversion": 1,
            "classname": "worldspawn",
            "maxpropscreenwidth": -1}
        # TODO: default skyname & detailmaterial/vbsp from config
        # use loaded world_settings, if they exist
        if "world" in nodes_dict:
            assert len(nodes_dict["world"]) == 1
            world_node = nodes_dict["world"][0]
            world_settings = {
                key: world_node.get(key, world_settings[key])
                for key in world_settings.keys()}

        world_node = Entity.as_node(worldspawn)
        world_node.node_type = "world"
        world_node.update(world_settings)
        new_nodes.append(world_node)
        # TODO: brush & brushside ids

        if len(self.entities) > 1:
            new_nodes.extend([
                Entity.as_node(entity)
                for entity in self.entities[1:]])
        # TODO: entity, brush & brushside ids

        if "cameras" in nodes_dict:
            assert len(nodes_dict["cameras"]) == 1
            cameras = nodes_dict["cameras"][0]
        else:
            cameras = Node("cameras")
            cameras["activecamera"] = -1
        new_nodes.append(cameras)

        if "cordon" in nodes_dict:
            cordons = nodes_dict["cordon"]
        else:
            cordon = Node("cordon")
            cordon.update({
                "mins": common.Point(-1024, -1024, -1024),
                "maxs": common.Point(+1024, +1024, +1024),
                "active": 0})
            cordons = [cordon]
        new_nodes.extend(cordons)

        self.nodes = new_nodes
