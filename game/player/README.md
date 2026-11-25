# player

The third-person player. Instance `player.tscn` with its origin where her feet go; she looks along the node's -Z, and the camera starts behind her. Its camera makes itself current.

- `player.gd` walks, runs, jumps (coyote time, jump buffer, short hop when jump is let go early) and climbs steps up to `step_height`. Her collision is a cylinder so she stands flat on step edges.
- `camera_rig.gd` orbits her and pulls in when walls or the ground come between.
- `air_ability.gd` is the slot for race-specific air movement: the `AirAbility` child gets every jump press in mid-air and drives her while active. `glide.gd` is the first: hold jump to float down. A race swaps in its own by replacing that child.
- `player_body.gd` is the visible body, the `Body` child. `placeholder_body.tscn` is a capsule that leans. The real character replaces it with a scene whose root extends `PlayerBody`, faces +Z, and passes `show_motion` on to its AnimationTree.
- `playground.tscn` is a test ground with a wall, ramps, stairs, blocks and ledges.

Controls, all actions in `../project.godot`:

| | Steam Deck | Keyboard and mouse |
|---|---|---|
| move | left stick (tilt to walk slowly) | WASD |
| run | hold B or L1 | hold Shift |
| jump, glide | A; again in mid-air and hold | Space |
| camera | right stick | mouse (click to capture, Esc frees), arrow keys |

Try it:

    py -3 tools/run/quiet.py --path game --fixed-fps 60 -s ../tools/run/drive.gd -- scene=res://player/playground.tscn out=build/drive/glide do="0.5:press:move_forward;1:press:jump;1.5:release:jump;1.6:press:jump;2.1:shot:glide;3:release:jump"
