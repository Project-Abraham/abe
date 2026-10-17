import pathlib

import abe
import bsp_tool
import decompile_rbsp


mod_path = pathlib.Path("/data/ssd1/Mod/")
bsp_path = mod_path / "Titanfall2/maps/"
map_path = mod_path / "_tools/Source Engine - Respawn/MRVN-Radiant_games/Titanfall2/maps/r2/"


for bsp_filename in bsp_path.glob("*.bsp"):
    # print(f"{bsp_filename=}")
    bsp = bsp_tool.load_bsp(str(bsp_filename))
    map_d = decompile_rbsp.decompile_map(bsp)
    map_filename = bsp_filename.stem + ".map"
    print(f"{map_filename=}")
    # print(f"{map_path / map_filename=}")
    v220_d = abe.Valve220Map.from_entities(map_filename, map_d.entities)
    v220_d.save_as(map_path / map_filename)
    print()
