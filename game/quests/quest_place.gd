class_name QuestPlace
extends QuestTarget
## A place a visit step sends the player to. She has been there once she comes within radius.

@export var radius := 8.0

var _world: World


func _ready() -> void:
	_world = World.of(self)


func _physics_process(_delta: float) -> void:
	if _world and _world.player and Quests.awaits_visit(id) \
			and global_position.distance_to(_world.player.global_position) <= radius:
		Quests.visit(id)
