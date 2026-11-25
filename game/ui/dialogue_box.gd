class_name DialogueBox
extends Control
## A conversation on a parchment at the bottom of the screen. Lines appear letter by letter; accept
## or interact shows the rest of a line, then the next one. Choices are buttons.

signal _next
signal _picked(index: int)

const LETTERS_PER_SECOND := 70.0

var _reveal: Tween
var _waiting := false

@onready var _name: Label = %Name
@onready var _text: Label = %Text
@onready var _choices: VBoxContainer = %Choices
@onready var _continue: ButtonHint = %Continue


## Talks with a speaker about one of its talks; with several, the player picks a topic first, and
## with none, the speaker says its greeting.
func converse(speaker: String, greeting: PackedStringArray, talks: Array[Quest.Talk]) -> void:
	_name.text = speaker
	show()
	if talks.size() == 1:
		await _play(talks[0], talks[0])
	elif talks.is_empty():
		for line in greeting:
			await _say(line)
	else:
		_show_line(greeting[0] if greeting else "")
		var topics: Array = talks.map(func(talk: Quest.Talk) -> String: return talk.topic)
		topics.append("Goodbye.")
		var picked := await _choose(topics)
		if picked < talks.size():
			await _play(talks[picked], talks[picked])
	hide()


func _play(passage: Quest.Passage, talk: Quest.Talk) -> void:
	for i in passage.lines.size():
		if i == passage.lines.size() - 1 and not passage.choices.is_empty():
			_show_line(passage.lines[i])
		else:
			await _say(passage.lines[i])
	if passage.then:
		Quests.act(talk, passage.then)
	while not passage.choices.is_empty():
		var choice := passage.choices[await _choose(passage.choices.map(
			func(option: Quest.Choice) -> String: return option.text))]
		await _play(choice, talk)
		if not choice.back:
			break


func _show_line(line: String) -> void:
	_text.text = line
	_text.visible_ratio = 0.0
	_reveal = create_tween()
	_reveal.tween_property(_text, ^"visible_ratio", 1.0, maxf(line.length() / LETTERS_PER_SECOND, 0.01))


## Shows a line and waits until the player has read it. The continue hint keeps its place while
## hidden, so the parchment keeps its size.
func _say(line: String) -> void:
	_show_line(line)
	_continue.modulate.a = 1.0
	_waiting = true
	await _next
	_waiting = false
	_continue.modulate.a = 0.0


## Offers the options once the line above them is shown in full.
func _choose(options: Array) -> int:
	if _reveal.is_running():
		await _reveal.finished
	for i in options.size():
		var button := Button.new()
		button.text = options[i]
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.pressed.connect(_picked.emit.bind(i))
		_choices.add_child(button)
	_choices.show()
	_choices.get_child(0).grab_focus()
	var picked: int = await _picked
	for button in _choices.get_children():
		_choices.remove_child(button)
		button.queue_free()
	_choices.hide()
	return picked


func _unhandled_input(event: InputEvent) -> void:
	if not visible or not (event.is_action_pressed(&"ui_accept") or event.is_action_pressed(&"interact")):
		return
	if _reveal.is_running():
		get_viewport().set_input_as_handled()
		_reveal.custom_step(3600.0)
	elif _waiting:
		get_viewport().set_input_as_handled()
		_next.emit()
