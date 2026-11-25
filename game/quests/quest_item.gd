class_name QuestItem
extends Interactable
## A thing a collect step asks for, such as a lost lantern; its id is the kind of thing. It shows
## only while a quest wants it, and key tells it apart from others of its kind in the save.

@export var key: StringName


func _ready() -> void:
	Quests.changed.connect(_refresh)
	_refresh()


func interact(_hud: Hud) -> void:
	Quests.collect(self)


func _refresh() -> void:
	visible = Quests.wants(self)
