import pathlib
import time

import abe
import bsp_tool
import decompile_rbsp


mod_dir = pathlib.Path("/data/ssd1/Mod/")
bsp_dir = mod_dir / "Titanfall2/maps/"
mrvn_dir = mod_dir / "_tools/Source Engine - Respawn/MRVN-Radiant_games/"
map_dir = mrvn_dir / "Titanfall2/maps/r2/"
tricoll_dir = mrvn_dir / "Titanfall2/models/tricoll/"

assert bsp_dir.exists()
assert map_dir.exists()
assert tricoll_dir.exists()

for bsp_filename in bsp_dir.glob("*.bsp"):
    print(f"Decompiling {bsp_filename.stem} ...")
    bsp = bsp_tool.load_bsp(str(bsp_filename))
    (tricoll_dir / bsp_filename.stem).mkdir(exist_ok=True)  # HACK

    # TODO: real slow, use datetime.timedelta
    start_time = time.monotonic_ns()
    map_d = decompile_rbsp.decompile_map(bsp)
    map_filename = bsp_filename.stem + ".map"
    end_time = time.monotonic_ns()
    run_time = (end_time - start_time) * 10**-9
    minutes = int(run_time / 60)
    seconds = run_time - (minutes * 60)
    print(f"decompiled in {minutes}m{seconds:.3f}s")

    start_time = time.monotonic_ns()
    v220_d = abe.Valve220Map.from_entities(map_filename, map_d.entities)
    v220_d.save_as(map_dir / map_filename)
    end_time = time.monotonic_ns()
    run_time = (end_time - start_time) * 10**-9
    print(f"saved as Valve220 format in {run_time:.3f}s")

    print()  # let the next block breathe
