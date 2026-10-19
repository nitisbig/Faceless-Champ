#version 330
uniform vec4 color;
uniform float opacity;
uniform float radius;
in vec2 point_uv;
in float alpha;
out vec4 pixel;
void main() {
    float distance=length(point_uv)*(radius+1.0)-radius;
    float a=clamp(0.5-distance/max(fwidth(distance),0.00001),0.0,1.0)*alpha*color.a*opacity;
    pixel=vec4(color.rgb*a,a);
}
