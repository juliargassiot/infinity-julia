class_name World
extends Node3D
## The world root. Streams its WorldArea children in and out around the camera and remembers which
## area gates are open, so a gate stays open when its area unloads and loads again.

signal gate_opened(id: StringName)

## An area loads when the camera comes this close to its edge, and unloads beyond unload_margin.
@export var load_margin := 60.0
@export var unload_margin := 100.0

var _open_gates := {}


## The World a node belongs to, or null outside one.
static func of(node: Node) -> World:
	while node and node is not World:
		node = node.get_parent()
	return node


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


## Areas around the camera load before the first frame; later ones load on background threads.
func _stream(blocking: bool) -> void:
	var camera := get_viewport().get_camera_3d()
	if not camera:
		return
	for area in get_children():
		if area is WorldArea:
			area.stream(camera.global_position, load_margin, unload_margin, blocking)
