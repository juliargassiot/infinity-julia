class_name PlayerBody
extends Node3D
## The player's visible body, with its front along +Z. The player turns it to face the way she
## moves and reports the motion every physics frame. A rigged character's scene root extends this
## and feeds the report into its AnimationTree.


## ground_speed and vertical_speed are in m/s; air_move is the active air ability's animation, or
## empty.
func show_motion(_ground_speed: float, _vertical_speed: float, _on_floor: bool, _air_move: StringName) -> void:
	pass
