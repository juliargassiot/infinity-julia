class_name Quest
extends RefCounted
## One quest, read from a JSON file in data/ named after its id; README.md describes the format.
## A quest is a list of steps with one objective each, and the talks villagers have about it.
## What the player gains, from a step or from the whole quest, are grants: an open gate, a thing,
## a familiar, an invitation. Quests hands them out; whichever system knows a kind takes them.

const FOLDER := "res://quests/data"
const OBJECTIVES: Array[StringName] = [&"talk", &"visit", &"collect"]
const OUTCOMES: Array[StringName] = [&"start", &"advance"]
## The moments a talk can belong to besides a step: before the quest starts and after it ends.
const OFFER := &"offer"
const DONE := &"done"

var id: StringName
var title := ""
var summary := ""
var main := false
var auto_start := false
var after: Array[StringName] = []
var steps: Array[Step] = []
## Granted when the quest is done.
var grants: Array[Grant] = []
var talks: Array[Talk] = []


static func load_all() -> Dictionary[StringName, Quest]:
	var quests: Dictionary[StringName, Quest] = {}
	for file in ResourceLoader.list_directory(FOLDER):
		if file.get_extension() != "json":
			continue
		var json: JSON = load(FOLDER.path_join(file))
		if json and json.data is Dictionary:
			var quest := Quest.new(file.get_basename(), json.data)
			quests[quest.id] = quest
		else:
			push_error("Quest: %s is not a quest" % file)
	for quest: Quest in quests.values():
		for problem in quest.problems(quests):
			push_error("Quest %s: %s" % [quest.id, problem])
	return quests


func _init(quest_id: String, data: Dictionary) -> void:
	id = quest_id
	title = data.get("title", quest_id.capitalize())
	summary = data.get("summary", "")
	main = data.get("main", false)
	auto_start = data.get("auto_start", false)
	after.assign(data.get("after", []))
	grants = Grant.list(data)
	for step: Dictionary in data.get("steps", []):
		steps.append(Step.new(step))
	for talk: Dictionary in data.get("talks", []):
		talks.append(Talk.new(self, talk))


func step_index(step_id: StringName) -> int:
	for i in steps.size():
		if steps[i].id == step_id:
			return i
	return -1


## What is wrong with the quest as written, so mistakes show when the game starts.
func problems(quests: Dictionary[StringName, Quest]) -> PackedStringArray:
	var found := PackedStringArray()
	if steps.is_empty():
		found.append("has no steps")
	for quest in after:
		if not quests.has(quest):
			found.append("comes after %s, which does not exist" % quest)
	var all_grants := grants.duplicate()
	for step in steps:
		all_grants.append_array(step.grants)
	for grant in all_grants:
		if not grant.kind:
			found.append("a grant needs a kind besides its name: %s" % grant.name)
	for step in steps:
		if step.kind not in OBJECTIVES:
			found.append("step %s needs one objective of %s" % [step.id, OBJECTIVES])
		elif step.kind == &"talk" and not talks.any(func(talk: Talk) -> bool:
				return talk.when == step.id and talk.person == step.target and &"advance" in talk.outcomes()):
			found.append("no talk with %s advances step %s" % [step.target, step.id])
	if not auto_start and not talks.any(func(talk: Talk) -> bool:
			return talk.when == OFFER and &"start" in talk.outcomes()):
		found.append("starts neither by itself nor through a talk")
	for talk in talks:
		if talk.when != OFFER and talk.when != DONE and step_index(talk.when) < 0:
			found.append("a talk with %s is for %s, which is no step" % [talk.person, talk.when])
		for outcome in talk.outcomes():
			if outcome not in OUTCOMES:
				found.append("a talk with %s leads to %s; outcomes are %s" % [talk.person, outcome, OUTCOMES])
	return found


class Step:
	var id: StringName
	## The task as the journal shows it.
	var task := ""
	## One of OBJECTIVES, and the person, place or kind of thing it is about.
	var kind: StringName
	var target: StringName
	## How many things a collect step asks for.
	var count := 1
	## Granted when the step is done.
	var grants: Array[Grant] = []

	func _init(data: Dictionary) -> void:
		id = data.get("id", "")
		task = data.get("task", "")
		count = int(data.get("count", 1))
		grants = Grant.list(data)
		for objective in OBJECTIVES:
			if data.has(objective):
				kind = objective
				target = data[objective]


## Lines spoken by whoever the player talks with, then what happens, then the player's choices.
class Passage:
	var lines := PackedStringArray()
	var choices: Array[Choice] = []
	## What reaching this passage does to its quest: one of OUTCOMES, or nothing.
	var then: StringName
	## After a chosen passage with back set, the choices it was picked from come again.
	var back := false

	func _init(data: Dictionary) -> void:
		lines = PackedStringArray(data.get("lines", []))
		then = data.get("then", "")
		back = data.get("back", false)
		for choice: Dictionary in data.get("choices", []):
			choices.append(Choice.new(choice))

	func outcomes() -> Array[StringName]:
		var all: Array[StringName] = []
		if then:
			all.append(then)
		for choice in choices:
			all.append_array(choice.outcomes())
		return all


class Choice extends Passage:
	var text := ""

	func _init(data: Dictionary) -> void:
		super(data)
		text = data.get("text", "")


## A conversation with one person at one moment of the quest: OFFER, a step's id, or DONE.
class Talk extends Passage:
	var quest: StringName
	var person: StringName
	var when: StringName
	## How the talk is offered when the person has several things to talk about.
	var topic := ""

	func _init(of: Quest, data: Dictionary) -> void:
		super(data)
		quest = of.id
		person = data.get("with", "")
		when = data.get("when", "")
		topic = data.get("topic", of.title)


## Something the player gains, written {"<kind>": "<id>", "name": "<as the player reads it>"}, such
## as {"gate": "witch_marsh"} or {"familiar": "moth_cat"}. The kind is any word; a system that
## knows it acts on Quests.granted.
class Grant:
	var kind: StringName
	var id: StringName
	var name := ""

	func _init(data: Dictionary) -> void:
		for key: String in data:
			if key != "name":
				kind = key
				id = data[key]
		name = data.get("name", String(id).capitalize())

	static func list(data: Dictionary) -> Array[Grant]:
		var all: Array[Grant] = []
		for grant: Dictionary in data.get("grants", []):
			all.append(Grant.new(grant))
		return all
