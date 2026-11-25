extends Node3D
## A gray-box playground for the player, on a one-metre checker: a wall behind the start for the
## camera, ramps of 15, 30 and 50 degrees (too steep) up to a plateau, stairs of 0.2 and 0.3 m
## steps up to another, blocks of 0.15, 0.3 and 0.45 m (too high to step), and ledges 1 to 4 m
## high to jump up and glide from.

const GROUND := Color(0.5, 0.68, 0.42)
const WALL := Color(0.93, 0.88, 0.8)
const RAMP := Color(0.92, 0.78, 0.55)
const STONE := Color(0.72, 0.72, 0.78)
const LEDGE := Color(0.78, 0.68, 0.9)

var _materials := {}


func _ready() -> void:
	_box(Vector3(80, 1, 80), Vector3(0, -0.5, 0), GROUND)
	_box(Vector3(8, 4, 0.5), Vector3(0, 2, 3), WALL)

	_box(Vector3(11, 2.5, 10), Vector3(-8.5, 1.25, -19), RAMP)
	for ramp in [[-12.0, 15.0], [-8.5, 30.0], [-5.0, 50.0]]:
		_ramp(ramp[0], deg_to_rad(ramp[1]), 2.5, -14.0)

	_box(Vector3(11, 2.4, 10), Vector3(8.5, 1.2, -19), STONE)
	_stairs(5.0, 0.2, 2.4, -14.0)
	_stairs(8.5, 0.3, 2.4, -14.0)
	for block in [[3.0, 0.15], [5.5, 0.3], [8.0, 0.45]]:
		_box(Vector3(2, block[1], 2), Vector3(block[0], block[1] / 2.0, -5), STONE)

	for i in 4:
		var height := i + 1.0
		_box(Vector3(2, height, 2), Vector3(18, height / 2.0, -4.0 - 2.5 * i), LEDGE)


## A ramp 2.5 m wide at x, rising toward -Z to top_height at top_z.
func _ramp(x: float, angle: float, top_height: float, top_z: float) -> void:
	const THICKNESS := 0.5
	var length := top_height / sin(angle)
	var middle := Vector3(x, top_height / 2.0, top_z + length * cos(angle) / 2.0)
	var normal := Vector3(0, cos(angle), sin(angle))
	_box(Vector3(2.5, THICKNESS, length), middle - normal * THICKNESS / 2.0, RAMP, angle)


## Stairs 2 m wide at x, rising toward -Z in steps of rise, 0.4 m deep, ending at top_height at top_z.
func _stairs(x: float, rise: float, top_height: float, top_z: float) -> void:
	const RUN := 0.4
	var steps := roundi(top_height / rise)
	for i in steps:
		var height := rise * (steps - i)
		_box(Vector3(2, height, RUN), Vector3(x, height / 2.0, top_z + RUN * (i + 0.5)), STONE)


func _box(size: Vector3, center: Vector3, color: Color, tilt := 0.0) -> void:
	var shape := BoxShape3D.new()
	shape.size = size
	var collision := CollisionShape3D.new()
	collision.shape = shape
	var mesh := BoxMesh.new()
	mesh.size = size
	mesh.material = _material(color)
	var visual := MeshInstance3D.new()
	visual.mesh = mesh
	var box := StaticBody3D.new()
	box.transform = Transform3D(Basis(Vector3.RIGHT, tilt), center)
	box.add_child(collision)
	box.add_child(visual)
	add_child(box)


func _material(color: Color) -> ShaderMaterial:
	if not _materials.has(color):
		var material := ShaderMaterial.new()
		material.shader = preload("res://player/grid.gdshader")
		material.set_shader_parameter("color", color)
		_materials[color] = material
	return _materials[color]
