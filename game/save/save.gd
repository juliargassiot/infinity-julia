extends Node
## The game's one save. Each system keeps a section of it: a Dictionary of plain data that JSON can
## hold (numbers come back as floats). A system reads its section when the save is loaded and
## writes it on saving; any system may call write() when something worth keeping happened.

## Systems read their sections again.
signal loaded
## Systems write their sections now; the file is written right after.
signal saving

const DEFAULT_FILE := "user://save.json"

## Where the game saves; empty for a game that is never written, as in scripted test runs.
var file := ""
var _sections := {}


func _ready() -> void:
	use(DEFAULT_FILE)


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		write()


## Plays from this save file, or a new game when it does not exist yet.
func use(path: String) -> void:
	file = path
	_sections = {}
	if path and FileAccess.file_exists(path):
		var read: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
		if read is Dictionary:
			_sections = read
		else:
			push_error("Save: %s is not a save file; starting a new game" % path)
	loaded.emit()


func section(name: String) -> Dictionary:
	return _sections.get_or_add(name, {})


func write() -> void:
	saving.emit()
	if not file:
		return
	var temporary := file + ".tmp"
	var out := FileAccess.open(temporary, FileAccess.WRITE)
	if not out:
		push_error("Save: cannot write %s (%s)" % [temporary, error_string(FileAccess.get_open_error())])
		return
	out.store_string(JSON.stringify(_sections, "\t"))
	out.close()
	DirAccess.rename_absolute(temporary, file)
