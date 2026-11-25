class_name ButtonHint
extends HBoxContainer
## What a button does, with the button as printed on the controller in use, or the key when the
## keyboard is in use.

const HINTS := &"button_hints"
## Steam Deck button labels by JoyButton.
const PAD_LABELS := {
	JOY_BUTTON_A: "A", JOY_BUTTON_B: "B", JOY_BUTTON_X: "X", JOY_BUTTON_Y: "Y",
	JOY_BUTTON_BACK: "View", JOY_BUTTON_START: "Menu",
	JOY_BUTTON_LEFT_SHOULDER: "L1", JOY_BUTTON_RIGHT_SHOULDER: "R1",
	JOY_BUTTON_DPAD_UP: "Up", JOY_BUTTON_DPAD_DOWN: "Down",
	JOY_BUTTON_DPAD_LEFT: "Left", JOY_BUTTON_DPAD_RIGHT: "Right",
}

static var gamepad := not Input.get_connected_joypads().is_empty()

@export var action: StringName
@export var text := "":
	set(value):
		text = value
		_label.text = value
@export var text_variation := &"Faded"

var _glyph := Label.new()
var _label := Label.new()


func _ready() -> void:
	add_to_group(HINTS)
	_glyph.theme_type_variation = &"Glyph"
	_glyph.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_label.theme_type_variation = text_variation
	_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(_glyph)
	add_child(_label)
	refresh()


func refresh() -> void:
	_glyph.text = label_of(action)


static func label_of(input_action: StringName) -> String:
	for event in InputMap.action_get_events(input_action):
		if gamepad and event is InputEventJoypadButton:
			return PAD_LABELS.get(event.button_index, str(event.button_index))
		if not gamepad and event is InputEventKey:
			return OS.get_keycode_string(event.physical_keycode if event.physical_keycode else event.keycode)
	return "?"


## Follows the last input: a controller's buttons or the keyboard's keys.
static func follow_input(event: InputEvent, tree: SceneTree) -> void:
	var on_gamepad := gamepad
	if event is InputEventJoypadButton or event is InputEventJoypadMotion and absf(event.axis_value) > 0.5:
		on_gamepad = true
	elif event is InputEventKey or event is InputEventMouseButton:
		on_gamepad = false
	if on_gamepad != gamepad:
		gamepad = on_gamepad
		tree.call_group(HINTS, &"refresh")
