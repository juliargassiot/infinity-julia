@tool
extends PlayerBody
## The player character: her rigged body, her look and what she wears.
##
## The character creator sets the three colors; they reach every mesh as per-instance shader
## parameters. Hair, clothing, jewelry and body features such as wings are pieces: scenes
## modelled in place on her rest pose, put on with wear().

const HairSprings := preload("res://characters/player/hair_springs.gd")

@export var skin_color := Color(0.97, 0.8, 0.72):
	set(value):
		skin_color = value
		_show_look()
@export var hair_color := Color(0.93, 0.62, 0.7):
	set(value):
		hair_color = value
		_show_look()
@export var eye_color := Color(0.36, 0.55, 0.92):
	set(value):
		eye_color = value
		_show_look()
@export var hairstyle: PackedScene = preload("res://characters/player/hair_flowing.glb"):
	set(value):
		hairstyle = value
		_show_hairstyle()
## What she wears until the wardrobe dresses her.
@export var placeholder_outfit: PackedScene = preload("res://characters/player/outfit_romper.glb")

## slot -> [the piece's nodes, the bits of the regions it covers]
var _worn := {}

@onready var _skeleton: Skeleton3D = $Model/Rig/Skeleton3D
@onready var _locomotion: AnimationTree = $Locomotion
## The names of the regions that can be hidden; a region's place in the list is its bit.
@onready var _regions: PackedStringArray = $Model/Rig/Skeleton3D/Body.get_meta(&"extras")["regions"].split(",")


func _ready() -> void:
	_show_hairstyle()
	wear(&"dress", placeholder_outfit, &"", [&"Chest", &"Waist", &"Hips"])


func show_motion(ground_speed: float, vertical_speed: float, on_floor: bool, air_move: StringName) -> void:
	_locomotion.show_motion(ground_speed, vertical_speed, on_floor, air_move)


## Puts a piece on her in place of what the slot held, and returns the piece's nodes. Without a
## bone, the piece's meshes are skinned to her skeleton: the piece was exported with her rig, or
## with the bones of it that it uses. With a bone, the whole piece rides on that bone: rigid
## jewelry on a socket, or a piece with a skeleton and animation of its own, such as a
## hairstyle, wings or a tail. covers names the regions the piece hides on her body and on
## everything else she wears.
func wear(slot: StringName, piece: PackedScene, bone := &"", covers: Array[StringName] = []) -> Array[Node]:
	take_off(slot)
	var instance := piece.instantiate()
	var nodes: Array[Node] = []
	if bone.is_empty():
		for mesh: MeshInstance3D in instance.find_children("*", "MeshInstance3D"):
			mesh.owner = null
			mesh.get_parent().remove_child(mesh)
			_skeleton.add_child(mesh)
			mesh.skeleton = NodePath("..")
			nodes.append(mesh)
		instance.free()
	else:
		socket(bone).add_child(instance)
		instance.transform = _skeleton.get_bone_global_rest(_skeleton.find_bone(bone)).affine_inverse()
		nodes.append(instance)
	var cover := 0
	for region in covers:
		cover |= 1 << _regions.find(region)
	_worn[slot] = [nodes, cover]
	_show_look()
	return nodes


func take_off(slot: StringName) -> void:
	if not _worn.has(slot):
		return
	for node: Node in _worn[slot][0]:
		node.queue_free()
	_worn.erase(slot)
	_show_look()


## The node that follows a bone of hers, for things that ride on it.
func socket(bone: StringName) -> BoneAttachment3D:
	var attachment_name := bone + "Attachment"
	var attachment := _skeleton.get_node_or_null(attachment_name) as BoneAttachment3D
	if attachment == null:
		attachment = BoneAttachment3D.new()
		attachment.name = attachment_name
		_skeleton.add_child(attachment)
		attachment.bone_name = bone
	return attachment


func _show_hairstyle() -> void:
	if not is_node_ready():
		return
	var hair := wear(&"hair", hairstyle, &"Head")[0]
	if not Engine.is_editor_hint():
		var springs := HairSprings.new()
		springs.body = _skeleton
		hair.find_child("Skeleton3D").add_child(springs)


## Gives every mesh her colors and hides what the other pieces cover.
func _show_look() -> void:
	if not is_node_ready():
		return
	for mesh: MeshInstance3D in _skeleton.find_children("*", "MeshInstance3D", true, false):
		if mesh.is_queued_for_deletion():
			continue
		var hidden := 0
		for worn: Array in _worn.values():
			if not worn[0].any(func(node: Node) -> bool: return node == mesh or node.is_ancestor_of(mesh)):
				hidden |= worn[1]
		mesh.set_instance_shader_parameter(&"skin_color", skin_color)
		mesh.set_instance_shader_parameter(&"hair_color", hair_color)
		mesh.set_instance_shader_parameter(&"eye_color", eye_color)
		mesh.set_instance_shader_parameter(&"hidden_regions", hidden)
