class_name Player
extends CharacterBody3D
## The player: walks, runs and jumps relative to the camera, and climbs steps. In mid-air, another
## jump press goes to her race's AirAbility child. Her origin is at her feet, and she starts out
## looking along her -Z.

@export_group("Ground")
@export var walk_speed := 3.0
@export var run_speed := 6.5
## How quickly her speed follows the stick, per second, when speeding up and when slowing down.
@export var acceleration := 9.0
@export var deceleration := 6.0
@export var turn_rate := 10.0
@export var step_height := 0.35

@export_group("Jump")
@export var jump_height := 1.3
@export var jump_rise_time := 0.42
## Gravity scales: lighter around the top of a jump, heavier when falling or when jump is let go
## early, for a short hop.
@export var apex_gravity_scale := 0.45
@export var apex_speed := 1.6
@export var fall_gravity_scale := 1.2
@export var short_hop_gravity_scale := 2.2
@export var max_fall_speed := 18.0
@export var air_control := 2.5
@export var coyote_time := 0.12
@export var jump_buffer := 0.12

## How quickly the body catches up after a step, per second.
const STEP_SMOOTHING := 14.0
## How far past her edge she looks for the top of a step, and how high above it she steps.
const STEP_REACH := 0.1
const STEP_CLEARANCE := 0.01

@onready var body: PlayerBody = $Body
@onready var air_ability: AirAbility = $AirAbility
@onready var camera: CameraRig = $CameraRig
@onready var _radius: float = ($Shape.shape as CylinderShape3D).radius

var _since_floor := INF
var _since_jump_press := INF


func _ready() -> void:
	floor_snap_length = step_height
	floor_constant_speed = true


func _physics_process(delta: float) -> void:
	var input := _move_input()
	_since_floor = 0.0 if is_on_floor() else _since_floor + delta
	var jump_pressed := Input.is_action_just_pressed("jump")
	_since_jump_press = 0.0 if jump_pressed else _since_jump_press + delta
	if _since_jump_press <= jump_buffer and _since_floor <= coyote_time:
		_jump()
	elif jump_pressed:
		air_ability.take_off()
	velocity = air_ability.move(velocity, input, delta) if air_ability.active else _walk_or_fall(input, delta)
	_step_up(delta)
	move_and_slide()
	if is_on_floor():
		air_ability.land()
	_turn_body(input, delta)
	body.show_motion(Vector2(velocity.x, velocity.z).length(), velocity.y, is_on_floor(),
		air_ability.animation if air_ability.active else &"")


## The move stick turned to follow the camera: world space, 0 to 1 long.
func _move_input() -> Vector3:
	var stick := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	return Basis(Vector3.UP, camera.yaw) * Vector3(stick.x, 0.0, stick.y)


func _walk_or_fall(input: Vector3, delta: float) -> Vector3:
	var target := input * (run_speed if Input.is_action_pressed("run") else walk_speed)
	var ground := Vector3(velocity.x, 0.0, velocity.z)
	var rate := air_control * input.length()
	if is_on_floor():
		rate = acceleration if target.length() > ground.length() else deceleration
	ground = ground.lerp(target, 1.0 - exp(-rate * delta))
	ground.y = maxf(velocity.y - _gravity() * delta, -max_fall_speed)
	return ground


func _jump() -> void:
	velocity.y = 2.0 * jump_height / jump_rise_time
	_since_floor = INF
	_since_jump_press = INF


func _gravity() -> float:
	var gravity := 2.0 * jump_height / (jump_rise_time * jump_rise_time)
	if velocity.y > 0.0 and not Input.is_action_pressed("jump"):
		return gravity * short_hop_gravity_scale
	if absf(velocity.y) < apex_speed:
		return gravity * apex_gravity_scale
	if velocity.y < 0.0:
		return gravity * fall_gravity_scale
	return gravity


## Lifts her onto a step she walks into, if it is no higher than step_height and its top is floor.
## A ray just past her edge finds the step's top; her collision shape is a cylinder, so she then
## stands flat on its edge. The body stays where it was and catches up smoothly.
func _step_up(delta: float) -> void:
	var motion := Vector3(velocity.x, 0.0, velocity.z) * delta
	var blocked := KinematicCollision3D.new()
	if not is_on_floor() or motion.is_zero_approx() or not test_move(global_transform, motion, blocked) \
			or blocked.get_angle() <= floor_max_angle:
		return
	var ahead := global_position + motion.normalized() * (_radius + STEP_REACH)
	var ray := PhysicsRayQueryParameters3D.create(ahead + Vector3.UP * step_height, ahead, collision_mask, [get_rid()])
	var top := get_world_3d().direct_space_state.intersect_ray(ray)
	if top.is_empty() or top.normal.angle_to(Vector3.UP) > floor_max_angle:
		return
	var climb: Vector3 = Vector3.UP * (top.position.y - global_position.y + STEP_CLEARANCE)
	if test_move(global_transform, climb) or test_move(global_transform.translated(climb), motion):
		return
	global_position += climb
	body.position -= climb


func _turn_body(input: Vector3, delta: float) -> void:
	if not input.is_zero_approx():
		var facing := atan2(input.x, input.z)
		body.global_rotation.y = lerp_angle(body.global_rotation.y, facing, 1.0 - exp(-turn_rate * delta))
	body.position.y = lerpf(body.position.y, 0.0, 1.0 - exp(-STEP_SMOOTHING * delta))
