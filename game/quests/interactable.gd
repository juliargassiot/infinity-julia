class_name Interactable
extends QuestTarget
## Something the player uses with the interact action when she is within reach. The HUD prompts
## for the nearest one.

const INTERACTABLES := &"interactables"

@export var display_name := ""
## The prompt reads "<verb> <display_name>".
@export var verb := "Talk to"
@export var reach := 2.4


func _enter_tree() -> void:
	super()
	add_to_group(INTERACTABLES)


func can_interact() -> bool:
	return is_visible_in_tree()


func prompt() -> String:
	return "%s %s" % [verb, display_name]


func interact(_hud: Hud) -> void:
	pass
