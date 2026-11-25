shader_type spatial;

// Set by terrain.gd: red is the height, green the distance to the nearest road edge.
uniform sampler2D heightmap : filter_linear, repeat_disable;
uniform float terrain_size = 640.0;
// The skirt continues the edges outward and sinks below the terrain inside them.
uniform bool skirt = false;

uniform sampler2D variation : filter_linear_mipmap, repeat_enable;
uniform float variation_scale = 70.0;
uniform vec3 grass_color : source_color = vec3(0.4, 0.62, 0.28);
uniform vec3 meadow_color : source_color = vec3(0.62, 0.7, 0.3);
uniform vec3 rock_color : source_color = vec3(0.55, 0.5, 0.46);
uniform vec3 sand_color : source_color = vec3(0.82, 0.74, 0.56);
uniform vec3 bed_color : source_color = vec3(0.3, 0.32, 0.26);
uniform vec3 road_color : source_color = vec3(0.76, 0.66, 0.52);
uniform float road_softness = 0.12;

varying vec2 map_uv;
varying vec3 world_position;

vec2 texel_center(vec2 xz, ivec2 samples) {
	return ((xz / terrain_size + 0.5) * vec2(samples - 1) + 0.5) / vec2(samples);
}

float height(ivec2 cell, ivec2 samples) {
	return texelFetch(heightmap, clamp(cell, ivec2(0), samples - 1), 0).r;
}

void vertex() {
	ivec2 samples = textureSize(heightmap, 0);
	ivec2 cell = ivec2(round((VERTEX.xz / terrain_size + 0.5) * vec2(samples - 1)));
	float spacing = terrain_size / float(samples.x - 1);
	VERTEX.y = height(cell, samples);
	if (skirt && all(lessThan(abs(VERTEX.xz), vec2(terrain_size * 0.5 - 1.0)))) {
		VERTEX.y -= 40.0;
	}
	NORMAL = normalize(vec3(
		height(cell - ivec2(1, 0), samples) - height(cell + ivec2(1, 0), samples),
		2.0 * spacing,
		height(cell - ivec2(0, 1), samples) - height(cell + ivec2(0, 1), samples)));
	map_uv = texel_center(VERTEX.xz, samples);
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 data = texture(heightmap, map_uv).rg;
	float slope = 1.0 - (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).y;
	float patches = texture(variation, world_position.xz / variation_scale).r;
	vec3 color = mix(grass_color, meadow_color, smoothstep(0.35, 0.75, patches));
	color = mix(color, rock_color, smoothstep(0.3, 0.5, slope));
	color = mix(color, sand_color, 1.0 - smoothstep(0.1, 0.6, data.r));
	color = mix(color, bed_color, 1.0 - smoothstep(-0.6, -0.1, data.r));
	float road = 1.0 - smoothstep(-road_softness, road_softness, data.g);
	ALBEDO = mix(color, road_color, road);
	ROUGHNESS = mix(0.95, 0.85, road);
}
