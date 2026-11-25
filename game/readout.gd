extends CanvasLayer

const REFRESH_SECONDS := 0.5
const MANIFEST := "manifest.json"

var _label := Label.new()
var _build := _read_build()
var _since_refresh := 0.0
var _frames := 0
var _slowest_frame := 0.0


func _ready() -> void:
	layer = 128
	process_mode = Node.PROCESS_MODE_ALWAYS
	var settings := LabelSettings.new()
	settings.font_size = 18
	settings.outline_size = 5
	settings.outline_color = Color(0, 0, 0, 0.75)
	_label.label_settings = settings
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_label.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT, Control.PRESET_MODE_MINSIZE, 12)
	_label.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_label)
	_refresh()


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("toggle_readout"):
		visible = not visible
		set_process(visible)
		_refresh()


func _process(delta: float) -> void:
	_frames += 1
	_since_refresh += delta
	_slowest_frame = maxf(_slowest_frame, delta)
	if _since_refresh >= REFRESH_SECONDS:
		_refresh()


func _refresh() -> void:
	var frame_rate := "-- fps"
	if _frames:
		frame_rate = "%d fps (low %d)" % [roundi(_frames / _since_refresh), roundi(1.0 / _slowest_frame)]
	_label.text = "%s\n%s" % [_build, frame_rate]
	_since_refresh = 0.0
	_frames = 0
	_slowest_frame = 0.0


static func _read_build() -> String:
	var path := OS.get_executable_path().get_base_dir().path_join(MANIFEST)
	if not FileAccess.file_exists(path):
		return "build dev"
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
	return "build %s  %s" % [manifest.version, manifest.get("date", "")]
