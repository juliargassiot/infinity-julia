# game

The Godot 4.7 project (Forward+ renderer). Open `project.godot` in Godot.

Everything here is original except folders named `third_party`, which hold downloaded assets together with their license files. Blender sources live in `../art`; only their exports belong here.

`player/` holds the player, her camera and a test ground.

`readout.gd` is an autoload that shows the build and the frame rate in the top-right corner; the `toggle_readout` action (`F3`) hides it. The build comes from `../tools/deck`.
