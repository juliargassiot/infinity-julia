@tool
class_name Terrain
extends Node3D
## The ground of the whole map: a heightmap drawn as one displaced grid, with matching collision.
## Its TerrainShape and TerrainPath children describe the landscape, and Bake turns them into the
## heightmap, whose red channel is the height and green the distance to the nearest road edge. Paths
## press in tree order, each into the ground the earlier ones left, so roads that come after ridges
## cut passes through them.

const ROAD_DISTANCE_LIMIT := 16.0
const ROAD_SMOOTHING_POINTS := 6
## The skirt carries the edge heights out to the horizon: it reaches this many terrain sizes past
## each edge, in cells of a terrain size over SKIRT_CELLS.
const SKIRT_REACH := 3
const SKIRT_CELLS := 8

@export var size := 640.0
@export var resolution := 257
@export_file("*.res") var heightmap_file := "res://world/terrain/heightmap.res"
@export var material: ShaderMaterial
@export var noise_seed := 1
@export_tool_button("Bake heightmap") var bake_action := bake

var _heightmap: Image
var _mesh := MeshInstance3D.new()
var _skirt := MeshInstance3D.new()
var _collision := CollisionShape3D.new()


func _ready() -> void:
	add_child(_mesh)
	_skirt.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_skirt)
	var body := StaticBody3D.new()
	body.add_child(_collision)
	add_child(body)
	if material and ResourceLoader.exists(heightmap_file):
		_show(load(heightmap_file))


## The ground height under a point in this node's space, between heightmap samples interpolated.
func height_at(x: float, z: float) -> float:
	var cell := Vector2(x, z) / _spacing() + Vector2.ONE * (resolution - 1) * 0.5
	var i := clampi(floori(cell.x), 0, resolution - 2)
	var j := clampi(floori(cell.y), 0, resolution - 2)
	var f := cell - Vector2(i, j)
	var top := lerpf(_heightmap.get_pixel(i, j).r, _heightmap.get_pixel(i + 1, j).r, f.x)
	var bottom := lerpf(_heightmap.get_pixel(i, j + 1).r, _heightmap.get_pixel(i + 1, j + 1).r, f.x)
	return lerpf(top, bottom, f.y)


func bake() -> void:
	var shapes: Array[TerrainShape] = []
	var paths: Array[TerrainPath] = []
	for node in find_children("*", "", true, false):
		if node is TerrainShape:
			shapes.append(node)
		elif node is TerrainPath:
			paths.append(node)
	var noise := FastNoiseLite.new()
	noise.seed = noise_seed
	noise.frequency = 1.0 / 90.0
	noise.fractal_octaves = 4
	var count := resolution * resolution
	var heights := PackedFloat32Array()
	heights.resize(count)
	var road_distance := PackedFloat32Array()
	road_distance.resize(count)
	road_distance.fill(ROAD_DISTANCE_LIMIT)
	for j in resolution:
		for i in resolution:
			var sample := _sample_position(i, j)
			heights[j * resolution + i] = _shape_height(sample.x, sample.y, shapes, noise)
	for path in paths:
		_press(path, _path_points(path, shapes, noise), heights, road_distance)
	var image := Image.create_empty(resolution, resolution, false, Image.FORMAT_RGF)
	for j in resolution:
		for i in resolution:
			var index := j * resolution + i
			image.set_pixel(i, j, Color(heights[index], road_distance[index], 0.0))
	var error := ResourceSaver.save(image, heightmap_file)
	if error != OK:
		push_error("Terrain: cannot save %s: %s" % [heightmap_file, error_string(error)])
	_show(image)


func _show(image: Image) -> void:
	_heightmap = image
	var mesh := PlaneMesh.new()
	mesh.size = Vector2.ONE * size
	mesh.subdivide_width = resolution - 2
	mesh.subdivide_depth = resolution - 2
	_mesh.mesh = mesh
	var drawn := material.duplicate() as ShaderMaterial
	drawn.set_shader_parameter("heightmap", ImageTexture.create_from_image(image))
	drawn.set_shader_parameter("terrain_size", size)
	_mesh.material_override = drawn
	var skirt := PlaneMesh.new()
	var skirt_cells := (2 * SKIRT_REACH + 1) * SKIRT_CELLS
	skirt.size = Vector2.ONE * size * (2 * SKIRT_REACH + 1)
	skirt.subdivide_width = skirt_cells - 1
	skirt.subdivide_depth = skirt_cells - 1
	_skirt.mesh = skirt
	_skirt.material_override = drawn.duplicate()
	_skirt.material_override.set_shader_parameter("skirt", true)
	var heights := image.duplicate()
	heights.convert(Image.FORMAT_RF)
	var span := Vector2(INF, -INF)
	for value in heights.get_data().to_float32_array():
		span = Vector2(minf(span.x, value), maxf(span.y, value))
	_mesh.custom_aabb = AABB(Vector3(-size * 0.5, span.x, -size * 0.5), Vector3(size, span.y - span.x, size))
	_skirt.custom_aabb = AABB(Vector3(-skirt.size.x * 0.5, span.x, -skirt.size.x * 0.5), Vector3(skirt.size.x, span.y - span.x, skirt.size.x))
	var shape := HeightMapShape3D.new()
	shape.update_map_data_from_image(heights, 0.0, 1.0 / _spacing())
	_collision.shape = shape
	_collision.scale = Vector3.ONE * _spacing()


func _spacing() -> float:
	return size / (resolution - 1)


func _sample_position(i: int, j: int) -> Vector2:
	return (Vector2(i, j) - Vector2.ONE * (resolution - 1) * 0.5) * _spacing()


## Markers blend with weights that stay flat near each one and fall off quickly past its radius.
static func _shape_height(x: float, z: float, shapes: Array[TerrainShape], noise: FastNoiseLite) -> float:
	var falloffs := PackedFloat32Array()
	for shape in shapes:
		falloffs.append(pow(Vector2(x - shape.position.x, z - shape.position.z).length() / shape.radius, 4.0))
	var nearest: float = Array(falloffs).min()
	var total := 0.0
	var height := 0.0
	var roughness := 0.0
	for k in shapes.size():
		var weight := exp(nearest - falloffs[k])
		total += weight
		height += weight * shapes[k].position.y
		roughness += weight * shapes[k].roughness
	return (height + roughness * noise.get_noise_2d(x, z)) / total


## The path as points in terrain space; a path that follows the ground takes the smoothed shape
## height along it.
static func _path_points(path: TerrainPath, shapes: Array[TerrainShape], noise: FastNoiseLite) -> PackedVector3Array:
	var points := path.curve.tessellate_even_length(5, 2.0)
	for k in points.size():
		points[k] = path.transform * points[k]
	if not path.follows_ground:
		return points
	var ground := PackedFloat32Array()
	for point in points:
		ground.append(_shape_height(point.x, point.z, shapes, noise))
	for k in points.size():
		var first := maxi(k - ROAD_SMOOTHING_POINTS, 0)
		var last := mini(k + ROAD_SMOOTHING_POINTS, points.size() - 1)
		var sum := 0.0
		for m in range(first, last + 1):
			sum += ground[m]
		points[k].y = sum / (last - first + 1)
	return points


## Presses one path into the heights: each sample within reach of a segment takes the height of its
## nearest point on the path.
func _press(path: TerrainPath, points: PackedVector3Array, heights: PackedFloat32Array,
		road_distance: PackedFloat32Array) -> void:
	var half := path.width * 0.5
	var reach := half + path.falloff
	var nearest := {}
	for k in points.size() - 1:
		var a := points[k]
		var b := points[k + 1]
		var low := Vector2i(_sample_index(Vector2(minf(a.x, b.x), minf(a.z, b.z)) - Vector2.ONE * reach).floor())
		var high := Vector2i(_sample_index(Vector2(maxf(a.x, b.x), maxf(a.z, b.z)) + Vector2.ONE * reach).ceil())
		for j in range(maxi(low.y, 0), mini(high.y, resolution - 1) + 1):
			for i in range(maxi(low.x, 0), mini(high.x, resolution - 1) + 1):
				var sample := _sample_position(i, j)
				var along := Vector2(b.x - a.x, b.z - a.z)
				var t := clampf((sample - Vector2(a.x, a.z)).dot(along) / maxf(along.length_squared(), 0.0001), 0.0, 1.0)
				var distance := sample.distance_to(Vector2(a.x, a.z) + along * t)
				var index := j * resolution + i
				if distance < nearest.get(index, Vector2(INF, 0.0)).x:
					nearest[index] = Vector2(distance, lerpf(a.y, b.y, t))
	for index: int in nearest:
		var hit: Vector2 = nearest[index]
		var weight := 1.0 - smoothstep(half, reach, hit.x)
		heights[index] = lerpf(heights[index], hit.y, weight)
		if path.paved:
			road_distance[index] = minf(road_distance[index], hit.x - half)


func _sample_index(point: Vector2) -> Vector2:
	return point / _spacing() + Vector2.ONE * (resolution - 1) * 0.5
