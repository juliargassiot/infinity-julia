shader_type spatial;
// Hair locks run root to tip along UV.y and across their width along UV.x. Vertex color: R a
// random value per lock, G 0 at the root to 1 at the tip, B the layer (0 underneath, 1 on top).

instance uniform vec3 hair_color : source_color, instance_index(1) = vec3(0.93, 0.62, 0.7);

uniform float root_shade : hint_range(0.0, 1.0) = 0.72;
uniform float tip_glow : hint_range(0.5, 1.5) = 1.12;
uniform float under_shade : hint_range(0.0, 1.0) = 0.62;
uniform float strands : hint_range(1.0, 60.0) = 14.0;
uniform float strand_contrast : hint_range(0.0, 0.5) = 0.16;
uniform float roughness : hint_range(0.0, 1.0) = 0.42;
uniform vec3 highlight_tint : source_color = vec3(1.0, 0.94, 0.9);
uniform float highlight_strength : hint_range(0.0, 3.0) = 0.45;
uniform float highlight_shift : hint_range(-1.0, 1.0) = 0.12;
uniform float highlight_width : hint_range(0.01, 0.5) = 0.11;
uniform float sky_highlight : hint_range(0.0, 1.0) = 0.12;

varying vec3 strand_direction;
varying float strand_shade;

float hash(float n) {
	return fract(sin(n) * 43758.5453);
}

float streaks(float across, float seed) {
	float cells = across * strands + seed * 37.0;
	return mix(hash(floor(cells) + seed * 91.0), hash(floor(cells) + 1.0 + seed * 91.0), smoothstep(0.0, 1.0, fract(cells)));
}

// A clean band where the strand lies across the half vector: Kajiya-Kay, squared off.
float band(vec3 tangent, vec3 half_vector) {
	float along = dot(tangent, half_vector);
	return smoothstep(highlight_width, 0.0, abs(along)) ;
}

void fragment() {
	strand_shade = streaks(UV.x, COLOR.r);
	vec3 base = hair_color * mix(root_shade, tip_glow, smoothstep(0.0, 0.85, COLOR.g));
	base *= mix(under_shade, 1.0, COLOR.b) * (0.94 + 0.12 * COLOR.r);
	base *= 1.0 - strand_contrast * (strand_shade - 0.5) * 2.0 * COLOR.b;
	ALBEDO = base;
	ROUGHNESS = roughness;
	SPECULAR = 0.05;

	strand_direction = normalize(BINORMAL + NORMAL * (highlight_shift + (strand_shade - 0.5) * 0.18));
	vec3 up = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz + VIEW);
	float ring = band(strand_direction, up) * clamp(dot(NORMAL, up), 0.0, 1.0);
	EMISSION = base * highlight_tint * ring * sky_highlight * COLOR.b;
}

void light() {
	float facing = dot(NORMAL, LIGHT);
	float wrapped = clamp((facing + 0.4) / 1.4, 0.0, 1.0);
	DIFFUSE_LIGHT += wrapped * ATTENUATION * LIGHT_COLOR / PI;
	float shine = band(strand_direction, normalize(LIGHT + VIEW)) * smoothstep(-0.1, 0.4, facing);
	SPECULAR_LIGHT += shine * highlight_strength * highlight_tint * ATTENUATION * LIGHT_COLOR / PI;
}
