#version 330
in vec2 in_uv;
uniform float time;
uniform mat4 mvp;
out vec2 uv;
out float elevation;
void main() {
    uv = in_uv;
    vec2 p = (uv*2.0-1.0)*3.14159265;
    elevation = 0.65*sin(2.0*p.x-time*1.8)*cos(2.0*p.y-time*1.1);
    gl_Position = mvp * vec4(p.x,elevation,p.y,1.0);
}
