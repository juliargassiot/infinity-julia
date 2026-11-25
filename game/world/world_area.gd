@tool
class_name WorldArea
extends Node3D
## One area of the map, such as the village or a race's land: a scene that the World loads while the
## camera is near and frees when it is far. The area's origin is its center; radius reaches its edge.

@export_file("*.tscn") var scene: String
@export var radius := 100.0

var _content: Node
var _loading := false


func _ready() -> void:
	if Engine.is_editor_hint() and scene:
		_show(load(scene))


## Distance from the area's edge to a point, measured across the ground.
func distance_to(point: Vector3) -> float:
	var offset := point - global_position
	return Vector2(offset.x, offset.z).length() - radius


func stream(viewer: Vector3, load_margin: float, unload_margin: float, blocking: bool) -> void:
	var distance := distance_to(viewer)
	if _loading:
		_finish_loading(distance <= unload_margin)
	elif not _content and distance <= load_margin:
		if blocking:
			_show(load(scene))
		else:
			ResourceLoader.load_threaded_request(scene, "PackedScene", true)
			_loading = true
	elif _content and distance > unload_margin:
		_content.queue_free()
		_content = null


func _finish_loading(wanted: bool) -> void:
	var status := ResourceLoader.load_threaded_get_status(scene)
	if status == ResourceLoader.THREAD_LOAD_IN_PROGRESS:
		return
	_loading = false
	if status != ResourceLoader.THREAD_LOAD_LOADED:
		push_error("WorldArea: cannot load %s" % scene)
		return
	var packed: PackedScene = ResourceLoader.load_threaded_get(scene)
	if wanted:
		_show(packed)


func _show(packed: PackedScene) -> void:
	_content = packed.instantiate()
	add_child(_content)
