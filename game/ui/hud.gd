class_name Hud
extends CanvasLayer
## The screen over the world: the followed quest, objective markers, notes when quests change, the
## prompt for the nearest thing to interact with, conversations and the journal. The game pauses
## while a conversation or the journal is open. Belongs inside a World, whose player it follows.

const NOTE_SECONDS := 3.5
## How far above or below her something can be and still be in reach.
const REACH_HEIGHT := 2.5
## The actions that may still be held from closing a conversation or the journal; the game waits
## until they are let go, so a press meant for the book does not make her jump.
const MENU_ACTIONS: Array[StringName] = [&"ui_accept", &"ui_cancel", &"interact", &"journal"]

var _world: World
var _focus: Interactable
var _mouse_mode := Input.MOUSE_MODE_VISIBLE

@onready var _tracker: Control = %Tracker
@onready var _tracker_title: Label = %TrackerTitle
@onready var _tracker_task: Label = %TrackerTask
@onready var _notes: VBoxContainer = %Notes
@onready var _prompt: Control = %Prompt
@onready var _prompt_hint: ButtonHint = %PromptHint
@onready var _dialogue: DialogueBox = %Dialogue
@onready var _journal: Journal = %Journal


## A step's task as the player reads it, with how many things a collect step has so far.
static func task_text(quest: Quest, index: int) -> String:
	var step := quest.steps[index]
	if step.kind != &"collect" or Quests.steps_done(quest.id) != index:
		return step.task
	return "%s (%d/%d)" % [step.task, Quests.collected_count(quest.id), step.count]


func _ready() -> void:
	_world = World.of(self)
	Quests.changed.connect(_show_tracked)
	Quests.started.connect(func(quest: Quest) -> void: note("New quest: %s" % quest.title))
	Quests.advanced.connect(func(quest: Quest) -> void: note("Next: %s" % Quests.current_step(quest.id).task))
	Quests.completed.connect(func(quest: Quest) -> void: note("Quest complete: %s" % quest.title))
	Quests.collected.connect(func(quest: Quest, item: QuestItem, count: int) -> void:
		note("%s %d of %d" % [item.display_name.capitalize(), count, Quests.current_step(quest.id).count]))
	Quests.granted.connect(func(grant: Quest.Grant) -> void: note(grant.name))
	_show_tracked()


func note(text: String) -> void:
	var pill := PanelContainer.new()
	pill.theme_type_variation = &"Pill"
	pill.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	pill.modulate.a = 0.0
	var label := Label.new()
	label.theme_type_variation = &"PillText"
	label.text = text
	pill.add_child(label)
	_notes.add_child(pill)
	var fade := pill.create_tween()
	fade.tween_property(pill, ^"modulate:a", 1.0, 0.3)
	fade.tween_interval(NOTE_SECONDS)
	fade.tween_property(pill, ^"modulate:a", 0.0, 0.6)
	fade.tween_callback(pill.queue_free)


func talk(speaker: Speaker) -> void:
	_pause()
	await _dialogue.converse(speaker.display_name, speaker.greeting, Quests.talks_with(speaker.id))
	await _resume()


func open_journal() -> void:
	_pause()
	await _journal.browse()
	await _resume()


func _process(_delta: float) -> void:
	if get_tree().paused:
		return
	_focus = _nearest_interactable()
	_prompt.visible = _focus != null
	if _focus:
		_prompt_hint.text = _focus.prompt()


func _input(event: InputEvent) -> void:
	ButtonHint.follow_input(event, get_tree())


func _unhandled_input(event: InputEvent) -> void:
	if get_tree().paused:
		return
	if event.is_action_pressed(&"interact") and _focus:
		get_viewport().set_input_as_handled()
		_focus.interact(self)
	elif event.is_action_pressed(&"journal"):
		get_viewport().set_input_as_handled()
		open_journal()


func _nearest_interactable() -> Interactable:
	if not _world or not _world.player:
		return null
	var nearest: Interactable
	var nearest_distance := INF
	for node in get_tree().get_nodes_in_group(Interactable.INTERACTABLES):
		var thing := node as Interactable
		var offset := thing.global_position - _world.player.global_position
		var distance := Vector2(offset.x, offset.z).length()
		if distance <= thing.reach and distance < nearest_distance and absf(offset.y) < REACH_HEIGHT \
				and thing.can_interact():
			nearest = thing
			nearest_distance = distance
	return nearest


func _show_tracked() -> void:
	var step := Quests.current_step(Quests.tracked)
	_tracker.visible = step != null
	if step:
		var quest := Quests.get_quest(Quests.tracked)
		_tracker_title.text = quest.title
		_tracker_task.text = task_text(quest, Quests.steps_done(quest.id))




func _pause() -> void:
	_prompt.hide()
	get_tree().paused = true
	_mouse_mode = Input.mouse_mode
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _resume() -> void:
	while MENU_ACTIONS.any(Input.is_action_pressed):
		await get_tree().process_frame
	get_tree().paused = false
	Input.mouse_mode = _mouse_mode
