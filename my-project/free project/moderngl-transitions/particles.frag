#version 330
in float alpha;
in vec3 color;
out vec4 frag;
void main() {
    float r = length(gl_PointCoord-0.5)*2.0;
    frag = vec4(color, alpha*(1.0-smoothstep(0.25,1.0,r)));
}
