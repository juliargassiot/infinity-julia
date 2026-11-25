# game

The Godot 4.7 project (Forward+ renderer). Open `project.godot` in Godot.

Everything here is original except folders named `third_party`, which hold downloaded assets together with their license files. Blender sources live in `../art`; only their exports belong here.

`main.tscn` is the game's start: the map, rooted in Crossroads Village, with the player at the village square. `world/` holds the map and how its areas load.

`player/` holds the player, her camera and a test ground.

`readout.gd` is an autoload that shows the build and the frame rate in the top-right corner; the `toggle_readout` action (`F3`) hides it. The build comes from `../tools/deck`.
