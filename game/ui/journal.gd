class_name Journal
extends Control
## The quest journal, an open book: the started quests on the left page, the one in focus on the
## right, with the steps reached so far. Accept follows a quest; cancel or journal closes the book.

signal _closed

const FOLLOWED := Color(0.62, 0.36, 0.1)

var _entries: Dictionary[StringName, Button] = {}

@onready var _list: VBoxContainer = %List
@onready var _title: Label = %QuestTitle
@onready var _state: Label = %State
@onready var _summary: Label = %Summary
@onready var _steps: VBoxContainer = %Steps
@onready var _rewards: Label = %Rewards
@onready var _follow: ButtonHint = %Follow


func browse() -> void:
	_fill()
	show()
	await _closed
	hide()


func _fill() -> void:
	for child in _list.get_children():
		_list.remove_child(child)
		child.queue_free()
	_entries.clear()
	var focus: Button
	for main in [true, false]:
		var quests := Quests.journal().filter(func(quest: Quest) -> bool: return quest.main == main)
		if quests.is_empty():
			continue
		var heading := Label.new()
		heading.theme_type_variation = &"Heading"
		heading.text = "The story" if main else "Side quests"
		_list.add_child(heading)
		for quest: Quest in quests:
			var entry := Button.new()
			entry.text = quest.title
			entry.alignment = HORIZONTAL_ALIGNMENT_LEFT
			entry.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
			entry.focus_entered.connect(_show.bind(quest))
			entry.pressed.connect(_follow_quest.bind(quest))
			_list.add_child(entry)
			_entries[quest.id] = entry
			if not focus or quest.id == Quests.tracked:
				focus = entry
	if focus:
		focus.grab_focus()
	else:
		_title.text = "No quests yet"
		_state.text = ""
		_summary.text = "Villagers and the notice board in the square have tasks for you."
		_clear_steps()
		_rewards.text = ""
		_follow.hide()
	_mark_followed()


func _show(quest: Quest) -> void:
	var done := Quests.status(quest.id) == Quests.Status.DONE
	_title.text = quest.title
	_state.text = "Completed" if done else "Following" if quest.id == Quests.tracked else "Under way"
	_summary.text = quest.summary
	_clear_steps()
	var reached := Quests.steps_done(quest.id) + (0 if done else 1)
	for i in reached:
		_steps.add_child(_step_line(Hud.task_text(quest, i), i < Quests.steps_done(quest.id)))
	var rewards := PackedStringArray()
	for grant in quest.grants:
		rewards.append(grant.name)
	_rewards.text = "Reward: %s" % ", ".join(rewards) if rewards else ""
	_follow.visible = not done and quest.id != Quests.tracked


func _follow_quest(quest: Quest) -> void:
	if Quests.status(quest.id) == Quests.Status.ACTIVE:
		Quests.track(quest.id)
		_show(quest)
		_mark_followed()


func _mark_followed() -> void:
	for id in _entries:
		for color in [&"font_color", &"font_focus_color", &"font_hover_color"]:
			if id == Quests.tracked:
				_entries[id].add_theme_color_override(color, FOLLOWED)
			else:
				_entries[id].remove_theme_color_override(color)


func _clear_steps() -> void:
	for child in _steps.get_children():
		_steps.remove_child(child)
		child.queue_free()


## A step as a line with a gem: hollow while under way, filled once done.
func _step_line(text: String, done: bool) -> Control:
	var line := HBoxContainer.new()
	line.add_theme_constant_override(&"separation", 14)
	var gem := Control.new()
	gem.custom_minimum_size = Vector2(16, 28)
	gem.draw.connect(func() -> void:
		var c := Vector2(8, 15)
		var points := PackedVector2Array([c + Vector2(0, -8), c + Vector2(6, 0), c + Vector2(0, 8), c + Vector2(-6, 0), c + Vector2(0, -8)])
		if done:
			gem.draw_colored_polygon(points, Color(0.62, 0.5, 0.42))
		else:
			gem.draw_polyline(points, Color(0.82, 0.56, 0.2), 2.5, true))
	var label := Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if done:
		label.theme_type_variation = &"Faded"
	line.add_child(gem)
	line.add_child(label)
	return line


func _unhandled_input(event: InputEvent) -> void:
	if visible and (event.is_action_pressed(&"ui_cancel") or event.is_action_pressed(&"journal")):
		get_viewport().set_input_as_handled()
		_closed.emit()
