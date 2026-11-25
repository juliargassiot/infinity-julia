extends Node
## The quest log, an autoload: every quest in data/, how far the player has come in each, and the
## one she follows. Progress lives in the "quests" section of the save and is saved at every change.

signal changed
signal started(quest: Quest)
## A step was done and the quest goes on.
signal advanced(quest: Quest)
signal completed(quest: Quest)
## The step collects count things of the item's kind so far.
signal collected(quest: Quest, item: QuestItem, count: int)
## A done step or a finished quest grants this; see Quest.Grant.
signal granted(grant: Quest.Grant)

enum Status { LOCKED, OFFERED, ACTIVE, DONE }

## The quest the tracker and objective markers follow.
var tracked := &""
var _quests := Quest.load_all()
## For each started quest: "step" (index), "count" (things collected for it), "found" (keys of the
## things collected), "done".
var _progress := {}


func _ready() -> void:
	Save.loaded.connect(_restore)
	Save.saving.connect(_store)
	_restore()


func get_quest(id: StringName) -> Quest:
	return _quests.get(id)


## Started quests, the main story first, then in the order they were started.
func journal() -> Array[Quest]:
	var started: Array[Quest] = []
	for id: StringName in _progress:
		started.append(_quests[id])
	return _main_first(started)


func status(id: StringName) -> Status:
	if _progress.has(id):
		return Status.DONE if _progress[id].done else Status.ACTIVE
	for before in _quests[id].after:
		if status(before) != Status.DONE:
			return Status.LOCKED
	return Status.OFFERED


## The step the quest is at, or null when it is not under way or there is no such quest.
func current_step(id: StringName) -> Quest.Step:
	if not _progress.has(id) or _progress[id].done:
		return null
	return _quests[id].steps[_progress[id].step]


## How many of the steps are done.
func steps_done(id: StringName) -> int:
	if not _progress.has(id):
		return 0
	return _quests[id].steps.size() if _progress[id].done else _progress[id].step


## How many things the current collect step has.
func collected_count(id: StringName) -> int:
	return _progress[id].count if _progress.has(id) else 0


## The talks a person has now, the main story first.
func talks_with(person: StringName) -> Array[Quest.Talk]:
	var found: Array[Quest.Talk] = []
	for quest in _main_first(_quests.values()):
		var moment := _moment(quest)
		for talk in quest.talks:
			if talk.person == person and talk.when == moment:
				found.append(talk)
	return found


## Whether the person has a quest to offer.
func offers(person: StringName) -> bool:
	return talks_with(person).any(func(talk: Quest.Talk) -> bool:
		return talk.when == Quest.OFFER and &"start" in talk.outcomes())


## What a passage of a talk leads to, once it is reached.
func act(talk: Quest.Talk, outcome: StringName) -> void:
	match outcome:
		&"start":
			if status(talk.quest) == Status.OFFERED:
				_start(_quests[talk.quest])
				_changed()
		&"advance":
			if current_step(talk.quest) and current_step(talk.quest).id == talk.when:
				_advance(_quests[talk.quest])
				_changed()


func track(id: StringName) -> void:
	tracked = id
	_changed()


## Whether a step under way waits for the player to come to this place.
func awaits_visit(place: StringName) -> bool:
	return not _steps_at(&"visit", place).is_empty()


func visit(place: StringName) -> void:
	var quests := _steps_at(&"visit", place)
	for quest in quests:
		_advance(quest)
	if quests:
		_changed()


## Whether a step under way asks for this thing.
func wants(item: QuestItem) -> bool:
	return _steps_at(&"collect", item.id).any(func(quest: Quest) -> bool:
		return item.key not in _progress[quest.id].found)


func collect(item: QuestItem) -> void:
	var quests := _steps_at(&"collect", item.id).filter(func(quest: Quest) -> bool:
		return item.key not in _progress[quest.id].found)
	for quest: Quest in quests:
		var progress: Dictionary = _progress[quest.id]
		progress.found.append(item.key)
		progress.count += 1
		collected.emit(quest, item, progress.count)
		if progress.count >= current_step(quest.id).count:
			_advance(quest)
	if quests:
		_changed()


static func _main_first(quests: Array) -> Array[Quest]:
	var ordered: Array[Quest] = []
	for main in [true, false]:
		for quest: Quest in quests:
			if quest.main == main:
				ordered.append(quest)
	return ordered


func _steps_at(kind: StringName, target: StringName) -> Array[Quest]:
	var found: Array[Quest] = []
	for id: StringName in _progress:
		var step := current_step(id)
		if step and step.kind == kind and step.target == target:
			found.append(_quests[id])
	return found


## Which talks apply to the quest now: Quest.OFFER, its current step's id, Quest.DONE, or none.
func _moment(quest: Quest) -> StringName:
	match status(quest.id):
		Status.OFFERED:
			return Quest.OFFER
		Status.ACTIVE:
			return current_step(quest.id).id
		Status.DONE:
			return Quest.DONE
	return &""


func _start(quest: Quest) -> void:
	_progress[quest.id] = {step = 0, count = 0, found = [], done = false}
	tracked = quest.id
	started.emit(quest)


func _advance(quest: Quest) -> void:
	var progress: Dictionary = _progress[quest.id]
	_grant(quest.steps[progress.step].grants)
	progress.step += 1
	progress.count = 0
	if progress.step < quest.steps.size():
		advanced.emit(quest)
		return
	progress.done = true
	if tracked == quest.id:
		tracked = _next_to_track()
	completed.emit(quest)
	_grant(quest.grants)
	_start_automatic()


func _grant(grants: Array[Quest.Grant]) -> void:
	for grant in grants:
		granted.emit(grant)


func _next_to_track() -> StringName:
	for quest in journal():
		if status(quest.id) == Status.ACTIVE:
			return quest.id
	return &""


func _start_automatic() -> void:
	for quest: Quest in _quests.values():
		if quest.auto_start and status(quest.id) == Status.OFFERED:
			_start(quest)


func _changed() -> void:
	changed.emit()
	Save.write()


func _restore() -> void:
	var saved := Save.section("quests")
	_progress = {}
	for id: String in saved.get("progress", {}):
		if _quests.has(StringName(id)):
			var progress: Dictionary = saved.progress[id]
			_progress[StringName(id)] = {step = int(progress.step), count = int(progress.count),
				found = progress.found.map(func(key: String) -> StringName: return StringName(key)),
				done = progress.done}
	tracked = saved.get("tracked", "")
	_start_automatic()
	changed.emit()


func _store() -> void:
	var saved := Save.section("quests")
	saved.progress = _progress.duplicate(true)
	saved.tracked = tracked
