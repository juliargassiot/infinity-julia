# quests

The `Quests` autoload (`quests.gd`) reads every quest in `data/`, keeps the player's progress in the save, and hands out grants. A quest is a JSON file named after its id:

- `title`, `summary`, `main` (the story, else a side quest), `after` (quests to finish first), `auto_start` (starts as soon as it may; otherwise a talk starts it).
- `steps`: each has an `id`, a journal `task`, and one objective: `"talk": "<person>"`, `"visit": "<place>"` or `"collect": "<kind>"` with a `count`.
- `grants`, on the quest or on a step: `{"<kind>": "<id>", "name": "..."}`, handed out when it is done. `gate` opens an area gate (the World takes it); `item` is shown only, for now. A new kind, such as `{"familiar": "moth_cat"}` or `{"invite": "moonlit_ball"}`, needs no change here: its system connects to `Quests.granted`.
- `talks`: what a person says `"with"` them `"when"` the quest is at `offer` (may start), a step id, or `done`. A talk has `lines`, then `then` (`start` or `advance`), then `choices`, each with `text` and the same fields again; `"back": true` returns to the choices. A person with several talks offers them as topics (`topic`, default the title). A talk step needs a talk that reaches `"then": "advance"`.

Mistakes are printed when the game starts. In the world, the ids are on these nodes, placed in an area scene:

- `Speaker` (`speaker.gd`): someone or something to talk to, such as the quest notice board; a golden gem turns over it while it offers a quest. `villager.tscn` is a placeholder person in her own colors.
- `QuestPlace`: a place a visit step needs, with a radius.
- `QuestItem`: a thing to collect, shown only while wanted, with a unique `key`; `moon_lantern.tscn` is one.

All three are `QuestTarget`s, which the objective marker points at.
