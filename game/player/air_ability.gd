class_name AirAbility
extends Node
## How the player moves through the air beyond a plain jump. Each race brings its own (fae fly,
## mermaids swim fast): the player's AirAbility child is the one in use. The player offers it every
## jump press in mid-air and, while it is active, hands it the motion.

## The animation the body plays while this ability is active.
@export var animation: StringName

var active := false


## Jump was pressed in mid-air; set active to take over.
func take_off() -> void:
	pass


## The player's velocity for this physics frame while active. input is the move stick in world
## space, 0 to 1 long.
func move(velocity: Vector3, _input: Vector3, _delta: float) -> Vector3:
	return velocity


func land() -> void:
	active = false
