shader_type spatial;

uniform vec3 color : source_color = vec3(0.7);

varying vec3 world_position;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 cell = floor(world_position + 0.001);
	ALBEDO = color * mix(0.86, 1.0, mod(cell.x + cell.y + cell.z, 2.0));
	ROUGHNESS = 0.85;
}
