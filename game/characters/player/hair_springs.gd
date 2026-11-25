extends SpringBoneSimulator3D
## Makes a hairstyle swing. Every chain of bones named Hair<Group>_1, _2, ... in the hairstyle's
## skeleton becomes a spring chain with its group's feel, and collides with spheres and capsules
## that follow the bones of her body.

## Group name prefix: stiffness, drag, gravity, radius of the chain's joints.
const FEEL := {
	"HairFront": [3.2, 0.55, 0.3, 0.012],
	"HairSide": [1.4, 0.45, 0.9, 0.016],
	"HairBack": [0.9, 0.4, 1.2, 0.022],
}
## Body bone, radius, height (0 for a sphere), offset in the bone's space (Y runs along the bone).
const COLLIDERS := [
	["Head", 0.098, 0.0, Vector3(0.0, 0.105, 0.012)],
	["Neck", 0.05, 0.16, Vector3(0.0, 0.03, 0.0)],
	["UpperChest", 0.105, 0.26, Vector3(0.0, 0.05, 0.0)],
	["Spine", 0.1, 0.3, Vector3(0.0, 0.08, 0.0)],
	["Hips", 0.125, 0.0, Vector3(0.0, 0.0, 0.0)],
	["LeftShoulder", 0.055, 0.2, Vector3(0.0, 0.08, 0.0)],
	["RightShoulder", 0.055, 0.2, Vector3(0.0, 0.08, 0.0)],
	["LeftUpperArm", 0.045, 0.3, Vector3(0.0, 0.12, 0.0)],
	["RightUpperArm", 0.045, 0.3, Vector3(0.0, 0.12, 0.0)],
]

## Her body's skeleton; set it before this node enters the tree.
var body: Skeleton3D

var _shapes: Array[SpringBoneCollision3D] = []


func _ready() -> void:
	for collider in COLLIDERS:
		var shape: SpringBoneCollision3D
		if collider[2] > 0.0:
			shape = SpringBoneCollisionCapsule3D.new()
			shape.radius = collider[1]
			shape.height = collider[2]
		else:
			shape = SpringBoneCollisionSphere3D.new()
			shape.radius = collider[1]
		add_child(shape)
		_shapes.append(shape)

	var skeleton := get_skeleton()
	var roots := []
	for bone in skeleton.get_bone_count():
		var bone_name := skeleton.get_bone_name(bone)
		if bone_name.begins_with("Hair") and bone_name.ends_with("_1"):
			roots.append(bone)
	setting_count = roots.size()
	for i in roots.size():
		var end: int = roots[i]
		while not skeleton.get_bone_children(end).is_empty():
			end = skeleton.get_bone_children(end)[0]
		var feel := _feel(skeleton.get_bone_name(roots[i]))
		set_root_bone(i, roots[i])
		set_end_bone(i, end)
		set_extend_end_bone(i, true)
		set_end_bone_direction(i, BONE_DIRECTION_FROM_PARENT)
		set_end_bone_length(i, skeleton.get_bone_rest(end).origin.length())
		set_stiffness(i, feel[0])
		set_drag(i, feel[1])
		set_gravity(i, feel[2])
		set_radius(i, feel[3])
		set_enable_all_child_collisions(i, true)


func _process(_delta: float) -> void:
	var from_body := global_transform.affine_inverse() * body.global_transform
	for i in COLLIDERS.size():
		var pose := body.get_bone_global_pose(body.find_bone(COLLIDERS[i][0]))
		_shapes[i].transform = from_body * pose.translated_local(COLLIDERS[i][3])


func _feel(bone_name: String) -> Array:
	for group: String in FEEL:
		if bone_name.begins_with(group):
			return FEEL[group]
	push_error("No hair feel for the bone ", bone_name)
	return FEEL.values()[0]
