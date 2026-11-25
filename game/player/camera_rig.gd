class_name CameraRig
extends Node3D
## Orbits the player it belongs to: the right stick or the mouse turns it, and it pulls in so that
## walls never come between the camera and her. It trails her a little, more so up and down, so
## jumps and steps feel soft. A click captures the mouse and free_mouse lets it go.

@export var distance := 4.5
@export var pivot_height := 1.45
@export var start_pitch := deg_to_rad(-14.0)
@export var min_pitch := deg_to_rad(-70.0)
@export var max_pitch := deg_to_rad(35.0)
## Turn speed at full stick, in radians per second, sideways and up and down.
@export var stick_speed := Vector2(2.8, 1.8)
@export var mouse_speed := 0.0025
## How quickly the camera catches up with her, per second, sideways and up and down.
@export var follow_rate := Vector2(12.0, 5.0)
## How quickly the camera moves back out after a wall pulled it in, per second.
@export var pull_out_rate := 3.0
@export var collision_radius := 0.25

@onready var _player: CollisionObject3D = get_parent()
@onready var _camera: Camera3D = $Camera

var yaw := 0.0
var pitch := 0.0
var _distance := 0.0
var _cast := PhysicsShapeQueryParameters3D.new()


func _ready() -> void:
	top_level = true
	yaw = _player.global_rotation.y
	pitch = start_pitch
	_distance = distance
	global_position = _pivot()
	var sphere := SphereShape3D.new()
	sphere.radius = collision_radius
	_cast.shape = sphere
	_cast.exclude = [_player.get_rid()]
	_camera.make_current()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("free_mouse"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	elif event is InputEventMouseButton and event.pressed:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	elif event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_turn(-event.screen_relative * mouse_speed)


func _physics_process(delta: float) -> void:
	var stick := Input.get_vector("camera_left", "camera_right", "camera_down", "camera_up")
	_turn(Vector2(-stick.x, stick.y) * stick.length() * stick_speed * delta)
	var pivot := _pivot()
	var sideways := 1.0 - exp(-follow_rate.x * delta)
	global_position = Vector3(lerpf(global_position.x, pivot.x, sideways),
		lerpf(global_position.y, pivot.y, 1.0 - exp(-follow_rate.y * delta)),
		lerpf(global_position.z, pivot.z, sideways))
	rotation = Vector3(pitch, yaw, 0.0)
	_avoid_walls(delta)


func _turn(by: Vector2) -> void:
	yaw = wrapf(yaw + by.x, -PI, PI)
	pitch = clampf(pitch + by.y, min_pitch, max_pitch)


func _pivot() -> Vector3:
	return _player.global_position + Vector3.UP * pivot_height


## Casts a sphere from the pivot out to the camera: a wall pulls the camera in at once, and it
## eases back out once the way is clear.
func _avoid_walls(delta: float) -> void:
	_cast.transform = Transform3D(Basis(), global_position)
	_cast.motion = global_basis.z * distance
	var clear := distance * get_world_3d().direct_space_state.cast_motion(_cast)[0]
	_distance = clear if clear < _distance else lerpf(_distance, clear, 1.0 - exp(-pull_out_rate * delta))
	_camera.position = Vector3(0.0, 0.0, _distance)
