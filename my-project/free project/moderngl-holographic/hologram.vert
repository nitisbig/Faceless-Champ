#version 330
in vec3 in_position;
in vec2 in_grid;
uniform mat4 mvp;
uniform mat4 model;
out vec2 grid;
out vec3 world;
void main() {
    vec4 p = model * vec4(in_position, 1.0);
    grid = in_grid;
    world = p.xyz;
    gl_Position = mvp * p;
}
