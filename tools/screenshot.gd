extends SceneTree


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 2:
		printerr("usage: godot --path game -s ../tools/screenshot.gd -- <res://scene.tscn> <out.png> [frames]")
		quit(2)
		return
	var frames := int(args[2]) if args.size() > 2 else 30
	if change_scene_to_file(args[0]) != OK:
		printerr("cannot load scene: ", args[0])
		quit(1)
		return
	for i in frames:
		await process_frame
	await RenderingServer.frame_post_draw
	var error := root.get_texture().get_image().save_png(args[1])
	quit(0 if error == OK else 1)
