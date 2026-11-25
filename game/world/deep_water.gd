class_name DeepWater
extends Area3D
## Water too deep to wade, with its surface at this node's height. A character whose feet sink more
## than wade_depth below the surface is carried back to where she last stood on dry ground. The
## shape must cover all the ground characters walk on, so it sees where they stand.

@export var wade_depth := 1.0

## Each character in the area and where it last stood on dry ground.
var _dry := {}


func _ready() -> void:
	body_exited.connect(func(body: Node3D) -> void: _dry.erase(body))


func _physics_process(_delta: float) -> void:
	var surface := global_position.y
	for body in get_overlapping_bodies():
		if body is not CharacterBody3D:
			continue
		var feet: float = body.global_position.y
		if feet < surface - wade_depth and _dry.has(body):
			body.global_position = _dry[body]
			body.velocity = Vector3.ZERO
			body.reset_physics_interpolation()
		elif feet >= surface and body.is_on_floor():
			_dry[body] = body.global_position
