class_name QuestTarget
extends Node3D
## Something an objective is about: a person to talk to, a place to visit, a kind of thing to
## collect. The objective marker floats over it while the followed quest's step names its id.

const TARGETS := &"quest_targets"

@export var id: StringName
## Where the objective marker floats, above the origin.
@export var marker_height := 2.6


func _enter_tree() -> void:
	add_to_group(TARGETS)


func marker_position() -> Vector3:
	return global_position + Vector3.UP * marker_height
