// Hides the parts of a surface that clothing covers. Each face carries the number of its region
// in UV2.x; hidden_regions has a bit for each number. A hidden face shrinks to a point.
instance uniform int hidden_regions : instance_index(3) = 0;

vec3 unless_hidden(vec3 vertex, vec2 region) {
	return ((hidden_regions >> int(region.x + 0.5)) & 1) == 1 ? vec3(0.0) : vertex;
}
