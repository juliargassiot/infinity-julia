extends PlayerBody
## Stands in for the real character: leans into her speed and tips forward to glide.

@export var lean_per_speed := deg_to_rad(1.6)
@export var glide_lean := deg_to_rad(28.0)
@export var lean_rate := 7.0

@onready var _lean: Node3D = $Lean


func show_motion(ground_speed: float, _vertical_speed: float, _on_floor: bool, air_move: StringName) -> void:
	var target := glide_lean if air_move == &"glide" else ground_speed * lean_per_speed
	var weight := 1.0 - exp(-lean_rate * get_physics_process_delta_time())
	_lean.rotation.x = lerp_angle(_lean.rotation.x, target, weight)
