from abe.parse import common
from abe.parse import valve


def test_rebuild_nodes():
    vmf = valve.Vmf("untitiled.vmf")
    assert len(vmf.entities) == 0

    vmf.rebuild_nodes()
    nodes_dict = vmf.nodes_by_type()

    assert "versioninfo" in nodes_dict
    assert len(nodes_dict["versioninfo"]) == 1
    version_info = nodes_dict["versioninfo"][0]
    assert version_info["editorversion"] == 400
    assert version_info["formatversion"] == 100
    assert version_info["mapversion"] == 1
    assert version_info["prefab"] == 0
    assert len(version_info.key_values) == 4
    assert len(version_info.nodes) == 0

    assert "visgroups" in nodes_dict
    assert len(nodes_dict["visgroups"]) == 1
    visgroups = nodes_dict["visgroups"][0]
    assert len(visgroups.key_values) == 0
    assert len(visgroups.nodes) == 0

    assert "viewsettings" in nodes_dict
    assert len(nodes_dict["viewsettings"]) == 1
    view_settings = nodes_dict["viewsettings"][0]
    assert view_settings["bShow3DGrid"] == 0
    assert view_settings["bShowGrid"] == 1
    assert view_settings["bShowLogicalGrid"] == 0
    assert view_settings["bSnapToGrid"] == 1
    assert view_settings["nGridSpacing"] == 16
    assert len(view_settings.key_values) == 5
    assert len(view_settings.nodes) == 0

    assert "world" in nodes_dict
    assert len(nodes_dict["world"]) == 1
    world_node = nodes_dict["world"][0]
    assert world_node["id"] == 1
    assert world_node["mapversion"] == 1
    assert world_node["classname"] == "worldspawn"
    assert world_node["maxpropscreenwidth"] == -1
    assert len(world_node.key_values) == 4
    assert len(world_node.nodes) == 0

    assert "entity" not in nodes_dict

    assert "cameras" in nodes_dict
    assert len(nodes_dict["cameras"]) == 1
    cameras = nodes_dict["cameras"][0]
    assert cameras["activecamera"] == -1
    assert len(cameras.key_values) == 1
    assert len(cameras.nodes) == 0

    assert "cordon" in nodes_dict
    assert len(nodes_dict["cordon"]) == 1
    cordon = nodes_dict["cordon"][0]
    assert cordon["mins"] == common.Point(-1024, -1024, -1024)
    assert cordon["maxs"] == common.Point(+1024, +1024, +1024)
    assert cordon["active"] == 0
    assert len(cordon.key_values) == 3
    assert len(cordon.nodes) == 0

    assert len(nodes_dict) == 6
