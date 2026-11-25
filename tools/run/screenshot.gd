extends "drive.gd"
## Renders a scene for [frames] frames (default 30) and saves a PNG. Run it with --fixed-fps 60;
## see README.md.

const SCREENSHOT_USAGE := "usage: -s ../tools/run/screenshot.gd -- <res://scene.tscn> <out.png> [frames]"


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 2:
		printerr(SCREENSHOT_USAGE)
		quit(2)
		return
	var frames := int(args[2]) if args.size() > 2 else 30
	play(args[0], [[frames, shot.bind(path(args[1]))]])
