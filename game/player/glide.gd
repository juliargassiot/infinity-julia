class_name Glide
extends AirAbility
## A floaty glide: press jump again in mid-air and hold it to drift slowly down and steer; without
## the stick she keeps drifting. Letting go falls; pressing again glides again.

@export var speed := 5.0
@export var fall_speed := 1.3
## How quickly the glide follows the stick, per second.
@export var steer_rate := 2.2
## How quickly a rise or fall settles into fall_speed, per second.
@export var settle_rate := 3.5


func take_off() -> void:
	active = true


func move(velocity: Vector3, input: Vector3, delta: float) -> Vector3:
	active = Input.is_action_pressed("jump")
	var steer := 1.0 - exp(-steer_rate * input.length() * delta)
	var drift := Vector3(velocity.x, 0.0, velocity.z).lerp(input * speed, steer)
	drift.y = lerpf(velocity.y, -fall_speed, 1.0 - exp(-settle_rate * delta))
	return drift
