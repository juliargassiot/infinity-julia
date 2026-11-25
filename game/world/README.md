# world

The map. `../main.tscn` is its root, a `World`: sky, sun, terrain, water, the player, and one `WorldArea` per area.

- `world_area.gd`: an area is its own scene in `areas/`, built around its origin (the area's center). The World loads it on a background thread when the camera comes within `load_margin` of its `radius` and frees it beyond `unload_margin`. Areas near the camera at start load before the first frame. A new area is a new scene plus a `WorldArea` entry.
- `area_gate.gd`: a natural gate on a road. `Closed` holds the obstacle and an invisible blocker, `Open` what replaces it. `World.open_gate(&"witch_marsh")`, or a quest's `gate` grant, opens one; the save keeps it. The ids are the land names.
- `terrain/`: one heightmap for the whole map with matching collision, and a skirt carrying its edges to the horizon. `TerrainShape` markers set the land's height, `TerrainPath` roads and the stream are pressed into it, and the Terrain's Bake button (inspector) rewrites `heightmap.res`. `Terrain.height_at()` gives the ground height.
- `blockout/`: the gray-box palette.

## Layout

Crossroads Village sits on a plateau at the center: a square with a fountain and signpost, the tailor's outfit shop, magic shop, inn, quest notice board, clock tower, windmill, an old tree and houses. North is -Z. Lands in their opening order, which grows spookier:

| | land | direction | gate |
|---|---|---|---|
| 1 | witch marsh | south, 80 m | broken bridge over the stream ravine |
| 2 | mermaid coast | west | rockslide |
| 3 | fae glade | east | enchanted fog |
| 4 | werewolf forest | northwest | fallen giant trees |
| 5 | vampire estate | northeast, on a crag | black-rose thorn wall |

All of it is gray-box.
