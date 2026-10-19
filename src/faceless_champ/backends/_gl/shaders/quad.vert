#version 330
uniform vec2 target_size;
uniform vec4 rect;
uniform mat3 transform;
out vec2 uv;
out vec2 local;
void main() {
    uv = vec2(gl_VertexID & 1, (gl_VertexID >> 1) & 1);
    local = rect.xy + uv * rect.zw;
    vec3 p = transform * vec3(local, 1.0);
    gl_Position = vec4(p.xy / target_size * 2.0 - 1.0, 0.0, 1.0);
}
