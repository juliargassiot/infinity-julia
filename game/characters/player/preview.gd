extends Node3D
## A small stage for judging the character: golden-hour sun, soft fill and a camera for each
## view. Options come as key=value arguments after the screenshot tool's own: view (a camera's
## name), speed and vertical (m/s), air (an air move, or anything else for a plain jump), and
## skin, hair and eyes (HTML colors).

const LOOKS := {"skin": &"skin_color", "hair": &"hair_color", "eyes": &"eye_color"}

@onready var _character: PlayerBody = $Character

var _options := {}


func _ready() -> void:
	get_viewport().msaa_3d = Viewport.MSAA_4X
	for argument in OS.get_cmdline_user_args():
		var pair := argument.split("=")
		if pair.size() == 2:
			_options[pair[0]] = pair[1]
	(get_node(_options.get("view", "ThreeQuarter")) as Camera3D).make_current()
	for look: String in LOOKS:
		if _options.has(look):
			_character.set(LOOKS[look], Color.html(_options[look]))


func _process(_delta: float) -> void:
	_character.show_motion(float(_options.get("speed", 0.0)), float(_options.get("vertical", 0.0)),
		not _options.has("air"), StringName(_options.get("air", "")))
