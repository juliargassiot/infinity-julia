shader_type spatial;
// The eyeball mesh's UVs are polar around the pupil; see art/characters/player/face.py.

instance uniform vec3 eye_color : source_color, instance_index(2) = vec3(0.36, 0.55, 0.92);

uniform float iris_size : hint_range(0.05, 0.9) = 0.58;
uniform float pupil_size : hint_range(0.05, 0.8) = 0.36;
uniform vec3 sclera_color : source_color = vec3(0.97, 0.96, 0.98);
uniform vec3 sclera_shade : source_color = vec3(0.72, 0.66, 0.74);
uniform float glow : hint_range(0.0, 1.0) = 0.22;

float hash(float n) {
	return fract(sin(n) * 43758.5453);
}

float fibers(float angle, float radius) {
	float cells = angle / TAU * 90.0;
	float cell = floor(cells);
	float streak = mix(hash(cell), hash(cell + 1.0), smoothstep(0.0, 1.0, fract(cells)));
	return mix(1.0, 0.72 + 0.5 * streak, smoothstep(0.3, 0.6, radius) * (1.0 - smoothstep(0.85, 1.0, radius)));
}

float spot(vec2 at, vec2 center, vec2 size) {
	return 1.0 - smoothstep(0.82, 1.0, length((at - center) / size));
}

void fragment() {
	vec2 at = (UV - 0.5) * 2.0 / iris_size;
	float radius = length(at);
	float iris = 1.0 - smoothstep(0.97, 1.03, radius);

	vec3 deep = eye_color * eye_color * 0.32;
	vec3 bright = mix(eye_color, vec3(1.0), 0.38) * 1.15;
	float height = smoothstep(-0.95, 0.75, at.y);
	vec3 color = mix(bright, deep, height);
	float crescent = smoothstep(0.1, -0.9, at.y) * smoothstep(1.0, 0.45, radius);
	color = mix(color, bright * 1.25, crescent * 0.55);
	color *= fibers(atan(at.y, at.x), radius);
	color = mix(color, deep * 0.35, smoothstep(0.8, 1.0, radius));
	float pupil = 1.0 - smoothstep(pupil_size - 0.05, pupil_size + 0.03, length(at * vec2(1.0, 0.92)));
	color = mix(color, deep * 0.12, pupil);
	color = mix(color, deep * 0.5, smoothstep(0.35, 1.05, at.y) * 0.75);

	float shade = 0.5 * smoothstep(1.0, 2.2, radius) + 0.6 * smoothstep(0.3, 1.6, at.y);
	vec3 white = mix(sclera_color, sclera_shade, clamp(shade, 0.0, 1.0));

	float catchlight = spot(at, vec2(-0.36, 0.42), vec2(0.27, 0.2)) + spot(at, vec2(0.34, -0.42), vec2(0.11, 0.09));
	catchlight = clamp(catchlight, 0.0, 1.0) * iris;

	ALBEDO = mix(white, color, iris);
	EMISSION = color * glow * iris + vec3(catchlight) * 1.1;
	ROUGHNESS = 0.12;
	SPECULAR = 0.5;
}
