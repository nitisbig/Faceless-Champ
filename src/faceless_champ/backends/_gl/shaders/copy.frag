#version 330
uniform sampler2D source;
uniform float opacity;
in vec2 uv;
out vec4 pixel;
void main() {
    vec4 a=texture(source,uv);
    float alpha=opacity==1.0?a.a:floor(a.a*opacity*255.0+0.5)/255.0;
    pixel=vec4(a.rgb*(alpha/max(a.a,0.00000001)),alpha);
}
