class_name AreaGate
extends Node3D
## A natural gate on the road into an area, such as a broken bridge or a thorn wall. Its child
## Closed holds what blocks the way and Open what replaces it; World.open_gate(id) switches them.

@export var id: StringName

@onready var _closed: Node3D = $Closed
@onready var _open: Node3D = $Open


func _ready() -> void:
	var world := World.of(self)
	if world:
		world.gate_opened.connect(_on_gate_opened)
	_show(world != null and world.is_gate_open(id))


func _on_gate_opened(opened: StringName) -> void:
	if opened == id:
		_show(true)


func _show(open: bool) -> void:
	_enable(_open, open)
	_enable(_closed, not open)


## A disabled branch is hidden and leaves the physics world.
static func _enable(branch: Node3D, on: bool) -> void:
	branch.visible = on
	branch.process_mode = Node.PROCESS_MODE_INHERIT if on else Node.PROCESS_MODE_DISABLED
