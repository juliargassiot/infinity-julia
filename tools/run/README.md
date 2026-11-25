# run

Runs the game for tests without showing a window. Run these from the repository root; relative output paths are relative to it, and `build/` is ignored by git.

- `quiet.py` runs Godot on a hidden Windows desktop, so test windows never appear on Julia's screen, also when several agents run at once. Use it in place of `godot`; it finds Godot itself (or `GODOT`). If it is stopped, Godot stops too. `--timing` first waits until no other Godot or Blender runs and holds later launches until it ends.
- `drive.gd` plays a scene on a timeline at 60 fps: `do="<seconds>:<event>;..."` with the events `press:<action>[:<strength>]`, `release:<action>`, `tap:<action>` (held 0.1 s), `shot:<name>` (saves `<out>_<name>.png`), and `times:start`, `times:stop` (prints frame times and writes `<out>_times.csv`). It quits after the last event. Actions come from the game's input map and go in as input events. Each run is a new game that is never saved; `save=<file>` plays from that save file and keeps it, so a second run can check what the first one saved.
- `screenshot.gd` is `drive.gd` taking one shot after a number of frames (default 30).

Both need `--fixed-fps 60`, which makes every run play out identically:

    py -3 tools/run/quiet.py --path game --fixed-fps 60 -s ../tools/run/screenshot.gd -- res://main.tscn build/shots/main.png
    py -3 tools/run/quiet.py --path game --fixed-fps 60 -s ../tools/run/drive.gd -- scene=res://main.tscn out=build/drive/walk do="0.5:press:ui_right;2:shot:moved;2:release:ui_right"

`--resolution 1280x800` matches the Steam Deck. For frame times, add `--timing` before and `--disable-vsync` after `quiet.py`, otherwise the display's refresh rate caps them; the `gpu_ms` column is the GPU's own time.

On the Iris Xe with D3D12, the hidden desktop renders pixel for pixel what a visible window does.
