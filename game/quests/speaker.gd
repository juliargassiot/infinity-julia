class_name Speaker
extends Interactable
## Someone or something to talk to, such as a villager or the quest notice board. Talking opens the
## talks the quests give its id now, or its greeting when there are none. A golden gem turns over
## it while it has a quest to offer.

const OFFER_MARK := preload("res://quests/offer_mark.tscn")

@export var greeting := PackedStringArray()

var _offer_mark: Node3D = OFFER_MARK.instantiate()


func _ready() -> void:
	_offer_mark.position.y = marker_height
	add_child(_offer_mark)
	Quests.changed.connect(_refresh)
	_refresh()


func interact(hud: Hud) -> void:
	hud.talk(self)


func _refresh() -> void:
	_offer_mark.visible = Quests.offers(id)
