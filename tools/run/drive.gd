extends SceneTree
## Scripted play: loads a scene, plays input actions on a timeline at 60 fps, takes screenshots
## and records frame times, then quits. Run it with --fixed-fps 60; see README.md.

const FPS := 60
const TAP_SECONDS := 0.1
const USAGE := "usage: -s ../tools/run/drive.gd -- scene=<res://scene.tscn> [out=<prefix>] [save=<file>] do=\"<seconds>:<event>;...\""

## The game plays from this save file and keeps it across runs; without one it is a new game that
## is never saved, so runs do not depend on each other.
var save_file := ""
var _out := ""
var _busy := 0
var _failed := false
var _times: FrameTimes


func _initialize() -> void:
	var args := {}
	for arg in OS.get_cmdline_user_args():
		var pair := arg.split("=", true, 1)
		args[pair[0]] = pair[1] if pair.size() > 1 else ""
	if not args.has("scene"):
		_quit_with_usage()
		return
	_out = path(args.get("out", "build/drive/drive"))
	save_file = path(args["save"]) if args.has("save") else ""
	var timeline := []
	for event in String(args.get("do", "")).split(";", false):
		var parsed := _parse(event.split(":"))
		if parsed.is_empty():
			printerr("drive: cannot read the event \"%s\"" % event)
			_quit_with_usage()
			return
		timeline.append_array(parsed)
	play(args["scene"], timeline)


## A path relative to the repository, the folder above the Godot project.
func path(relative_or_absolute: String) -> String:
	if relative_or_absolute.is_absolute_path():
		return relative_or_absolute
	return ProjectSettings.globalize_path("res://").path_join("..").path_join(relative_or_absolute).simplify_path()


## Loads the scene and runs the timeline: a list of [frame, Callable]. Events due in the same
## frame run in list order.
func play(scene: String, timeline: Array) -> void:
	await process_frame
	var save := root.get_node_or_null(^"Save")
	if save:
		save.use(save_file)
	if change_scene_to_file(scene) != OK:
		printerr("drive: cannot load the scene ", scene)
		quit(1)
		return
	var due := {}
	for event in timeline:
		due.get_or_add(event[0], []).append(event[1])
	var frame := 0
	while not due.is_empty():
		for event: Callable in due.get(frame, []):
			event.call()
		due.erase(frame)
		await process_frame
		frame += 1
	while _busy > 0:
		await process_frame
	stop_times()
	quit(1 if _failed else 0)


func _parse(event: PackedStringArray) -> Array:
	if event.size() < 3 or not event[0].is_valid_float() or float(event[0]) < 0.0:
		return []
	var frame := roundi(float(event[0]) * FPS)
	var name := event[2]
	match [event[1], event.size()]:
		["press", 3]:
			return [[frame, press.bind(name, 1.0)]]
		["press", 4]:
			return [[frame, press.bind(name, float(event[3]))]]
		["release", 3]:
			return [[frame, release.bind(name)]]
		["tap", 3]:
			return [[frame, press.bind(name, 1.0)],
				[frame + roundi(TAP_SECONDS * FPS), release.bind(name)]]
		["shot", 3]:
			return [[frame, shot.bind("%s_%s.png" % [_out, name])]]
		["times", 3] when name == "start":
			return [[frame, start_times]]
		["times", 3] when name == "stop":
			return [[frame, stop_times]]
	return []


func _quit_with_usage() -> void:
	printerr(USAGE)
	quit(2)


## Actions go in as input events, as a controller's would, so the game's input handlers see them.
func press(action: String, strength: float) -> void:
	_send(action, true, strength)


func release(action: String) -> void:
	_send(action, false, 0.0)


func _send(action: String, pressed: bool, strength: float) -> void:
	if not InputMap.has_action(action):
		printerr("drive: the input map has no action ", action)
		_failed = true
		return
	var event := InputEventAction.new()
	event.action = action
	event.pressed = pressed
	event.strength = strength
	Input.parse_input_event(event)


## Saves the frame being drawn now.
func shot(file: String) -> void:
	_busy += 1
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(file.get_base_dir())
	var error := root.get_texture().get_image().save_png(file)
	print("shot: ", file, " ", error_string(error))
	_failed = _failed or error != OK
	_busy -= 1


func start_times() -> void:
	stop_times()
	_times = FrameTimes.new(root.get_viewport_rid())


## Prints a summary of the frames since start_times and writes each one to <out>_times.csv.
func stop_times() -> void:
	if _times:
		_times.stop("%s_times.csv" % _out)
		_times = null


class FrameTimes:
	var _viewport: RID
	var _last := 0
	var _rows := PackedStringArray(["frame,ms,gpu_ms,cpu_ms"])
	var _wall := PackedFloat64Array()
	var _gpu := 0.0

	func _init(viewport: RID) -> void:
		_viewport = viewport
		RenderingServer.viewport_set_measure_render_time(_viewport, true)
		RenderingServer.frame_post_draw.connect(_sample)
		_last = Time.get_ticks_usec()

	func _sample() -> void:
		var now := Time.get_ticks_usec()
		var wall := (now - _last) / 1000.0
		_last = now
		var gpu := RenderingServer.viewport_get_measured_render_time_gpu(_viewport)
		var cpu := RenderingServer.viewport_get_measured_render_time_cpu(_viewport) + RenderingServer.get_frame_setup_time_cpu()
		_rows.append("%d,%.3f,%.3f,%.3f" % [_wall.size(), wall, gpu, cpu])
		_wall.append(wall)
		_gpu += gpu

	func stop(file: String) -> void:
		RenderingServer.frame_post_draw.disconnect(_sample)
		RenderingServer.viewport_set_measure_render_time(_viewport, false)
		var count := _wall.size()
		if count == 0:
			return
		var total := 0.0
		for wall in _wall:
			total += wall
		var sorted := _wall.duplicate()
		sorted.sort()
		DirAccess.make_dir_recursive_absolute(file.get_base_dir())
		FileAccess.open(file, FileAccess.WRITE).store_string("\n".join(_rows) + "\n")
		print("times: %d frames, average %.2f ms (%.0f fps), 99th percentile %.2f ms, worst %.2f ms, gpu %.2f ms -> %s" % [
			count, total / count, 1000.0 * count / total, sorted[int(count * 0.99)], sorted[-1], _gpu / count, file])
