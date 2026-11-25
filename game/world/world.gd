class_name World
extends Node3D
## The world root. Streams its WorldArea children in and out around the camera and remembers which
## area gates are open, so a gate stays open when its area unloads and loads again. Quests open
## gates; the open gates and where the player stands are kept in the "world" section of the save.

signal gate_opened(id: StringName)

## An area loads when the camera comes this close to its edge, and unloads beyond unload_margin.
@export var load_margin := 60.0
@export var unload_margin := 100.0
## The player, a child of the World.
@export var player: Node3D

var _open_gates := {}


## The World a node belongs to, or null outside one.
static func of(node: Node) -> World:
	while node and node is not World:
		node = node.get_parent()
	return node


## Before the children are ready, so the player's camera and the first areas start where she was.
func _enter_tree() -> void:
	var saved := Save.section("world")
	for id: String in saved.get("gates", []):
		_open_gates[StringName(id)] = true
	if player and saved.has("player"):
		var place: Array = saved.player
		player.position = Vector3(place[0], place[1], place[2])
		player.rotation.y = place[3]
	Save.saving.connect(_save)
	Quests.granted.connect(_on_granted)


func _exit_tree() -> void:
	Save.saving.disconnect(_save)
	Quests.granted.disconnect(_on_granted)


func _ready() -> void:
	_stream(true)


func _process(_delta: float) -> void:
	_stream(false)


func is_gate_open(id: StringName) -> bool:
	return _open_gates.has(id)


func open_gate(id: StringName) -> void:
	if not is_gate_open(id):
		_open_gates[id] = true
		gate_opened.emit(id)


## Quests open gates with grants of the kind "gate".
func _on_granted(grant: Quest.Grant) -> void:
	if grant.kind == &"gate":
		open_gate(grant.id)


## She is saved facing the way the camera looks, which is where her camera starts.
func _save() -> void:
	var saved := Save.section("world")
	saved.gates = _open_gates.keys()
	var camera := get_viewport().get_camera_3d()
	if player and camera:
		saved.player = [player.position.x, player.position.y, player.position.z, camera.global_rotation.y]


## Areas around the camera load before the first frame; later ones load on background threads.
func _stream(blocking: bool) -> void:
	var camera := get_viewport().get_camera_3d()
	if not camera:
		return
	for area in get_children():
		if area is WorldArea:
			area.stream(camera.global_position, load_margin, unload_margin, blocking)
