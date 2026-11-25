# world

The map. `../main.tscn` is its root, a `World`: sky, sun, terrain, water, the player, and one `WorldArea` per area.

- `world_area.gd`: an area is its own scene in `areas/`, built around its center. The World loads it in the background when the camera comes within `load_margin` of its `radius`, frees it beyond `unload_margin`; nearby areas load before the first frame. A new area is a scene plus a `WorldArea`.
- `area_gate.gd`: a natural gate: `Closed` holds the obstacle and an invisible blocker, `Open` what replaces it. A quest's `gate` grant or `World.open_gate(id)` opens one; the save keeps it.
- `terrain/`: one heightmap with collision and an edge skirt. `TerrainShape` markers set heights, then `TerrainPath` ridges, roads and the stream are pressed in; the Terrain's Bake button rewrites `heightmap.res`; `Terrain.height_at()` gives ground height.
- `deep_water.gd`: whoever sinks a meter under water returns to where she last stood dry.
- `blockout/`: the gray-box palette.

## Layout

Crossroads Village sits on a plateau at the center: square, fountain, signpost, tailor, magic shop, inn, notice board, clock tower, windmill, old tree, houses. North is -Z. Lands in opening order, growing spookier:

| | land | direction | gate |
|---|---|---|---|
| 1 | witch marsh | south, across the stream | broken bridge |
| 2 | mermaid coast | west | rockslide |
| 3 | fae glade | east | enchanted fog |
| 4 | werewolf forest | northwest | fallen giant trees |
| 5 | vampire estate | northeast, on a crag | black-rose thorn wall |

Cliff ridges (`Terrain/Ridges`) wall in the village and each land, higher than anything reachable nearby, so neither walking nor gliding passes a gate; the deep stream, a border ridge and the sea guard the map's edge. All gray-box.
