class_name ObjectiveMarker
extends Control
## Golden gems over whatever the followed quest's step is about, with how far it is. Out of view,
## the gem waits at the screen's edge with a point toward it.

const GOLD := Color(1.0, 0.8, 0.38)
const INK := Color(0.26, 0.12, 0.26, 0.9)
## How far in from the screen's edge a gem waits.
const EDGE := 56.0

var _world: World


func _ready() -> void:
	_world = World.of(self)


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	var step := Quests.current_step(Quests.tracked)
	var camera := get_viewport().get_camera_3d()
	if not step or not camera or not _world or not _world.player:
		return
	for node in get_tree().get_nodes_in_group(QuestTarget.TARGETS):
		var target := node as QuestTarget
		if target.id == step.target and target.is_visible_in_tree():
			_draw_marker(camera, target)


func _draw_marker(camera: Camera3D, target: QuestTarget) -> void:
	var spot := target.marker_position()
	var area := get_viewport_rect().grow(-EDGE)
	var point := camera.unproject_position(spot)
	var behind := camera.is_position_behind(spot)
	var bob := Vector2(0.0, 4.0 * sin(Time.get_ticks_msec() / 300.0))
	if not behind and area.has_point(point):
		_draw_gem(point + bob, 1.0)
		var meters := Vector2(spot.x - _world.player.global_position.x, spot.z - _world.player.global_position.z).length()
		_draw_label(point + Vector2(0.0, 40.0), "%d m" % roundi(meters))
		return
	var center := area.get_center()
	var way := (center - point if behind else point - center).normalized()
	var half := area.size / 2.0
	var edge := center + way * minf(half.x / maxf(absf(way.x), 0.001), half.y / maxf(absf(way.y), 0.001))
	_draw_gem(edge, 0.8)
	var tip := edge + way * 30.0
	var side := way.orthogonal() * 9.0
	draw_colored_polygon(PackedVector2Array([tip, edge + way * 18.0 + side, edge + way * 18.0 - side]), GOLD)


func _draw_gem(at: Vector2, size: float) -> void:
	var outline := _diamond(at, 13.0 * size, 19.0 * size)
	draw_colored_polygon(_diamond(at, 20.0 * size, 28.0 * size), Color(GOLD, 0.25))
	draw_colored_polygon(outline, GOLD)
	outline.append(outline[0])
	draw_polyline(outline, INK, 2.0, true)
	draw_colored_polygon(_diamond(at + Vector2(-2.0, -4.0) * size, 4.0 * size, 6.0 * size), Color(1, 1, 0.92))


func _draw_label(at: Vector2, text: String) -> void:
	var font := get_theme_default_font()
	var size := 20
	var width := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	var baseline := at + Vector2(-width / 2.0, 0.0)
	draw_string_outline(font, baseline, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, 6, INK)
	draw_string(font, baseline, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(1, 0.96, 0.86))


static func _diamond(at: Vector2, half_width: float, half_height: float) -> PackedVector2Array:
	return PackedVector2Array([at + Vector2(0, -half_height), at + Vector2(half_width, 0),
		at + Vector2(0, half_height), at + Vector2(-half_width, 0)])
