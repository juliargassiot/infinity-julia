extends AnimationTree
## Blends her animations by how she moves: standing, walking and running on the ground, rising
## and falling in the air, and gliding.

## The ground speeds the walk and run cycles were keyed for, in m/s.
const WALK_SPEED := 3.0
const RUN_SPEED := 6.5
## The vertical speed, in m/s, at which she is fully in her rising or her falling pose.
const AIR_SPEED := 4.0
const BLEND_TIME := 0.18

var _state := &""


func _ready() -> void:
	var ground := AnimationNodeBlendSpace1D.new()
	ground.min_space = 0.0
	ground.max_space = RUN_SPEED
	ground.sync = true
	ground.add_blend_point(_clip(&"idle"), 0.0, -1, &"idle")
	ground.add_blend_point(_clip(&"walk"), WALK_SPEED, -1, &"walk")
	ground.add_blend_point(_clip(&"run"), RUN_SPEED, -1, &"run")
	var air := AnimationNodeBlendSpace1D.new()
	air.min_space = -AIR_SPEED
	air.max_space = AIR_SPEED
	air.add_blend_point(_clip(&"fall"), -AIR_SPEED, -1, &"fall")
	air.add_blend_point(_clip(&"rise"), AIR_SPEED, -1, &"rise")

	var state := AnimationNodeTransition.new()
	state.xfade_time = BLEND_TIME
	var tree := AnimationNodeBlendTree.new()
	tree.add_node(&"state", state)
	var inputs := {&"ground": ground, &"air": air, &"glide": _clip(&"glide")}
	for input: StringName in inputs:
		state.add_input(input)
		tree.add_node(input, inputs[input])
		tree.connect_node(&"state", state.get_input_count() - 1, input)
	tree.connect_node(&"output", 0, &"state")
	tree_root = tree
	active = true
	show_motion(0.0, 0.0, true, &"")


func show_motion(ground_speed: float, vertical_speed: float, on_floor: bool, air_move: StringName) -> void:
	var state := &"ground" if on_floor else (&"glide" if air_move == &"glide" else &"air")
	if state != _state:
		_state = state
		set(&"parameters/state/transition_request", state)
	set(&"parameters/ground/blend_position", ground_speed)
	set(&"parameters/air/blend_position", vertical_speed)


func _clip(animation: StringName) -> AnimationNodeAnimation:
	var node := AnimationNodeAnimation.new()
	node.animation = animation
	return node
