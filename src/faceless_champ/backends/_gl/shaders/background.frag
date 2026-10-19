#version 330
uniform float time;
uniform int kind;
uniform vec4 color;
uniform float opacity;
in vec2 uv;
out vec4 pixel;
void main() {
    float f=sin(uv.x*8.0+time)*sin(uv.y*6.0-time*0.7);
    if(kind==0)f=exp(-pow((uv.y-0.45-0.15*sin(uv.x*7.0+time))/0.18,2.0))*(0.7+0.3*f);
    else f=0.5+0.5*f;
    float a=color.a*opacity;
    pixel=vec4(clamp(color.rgb*(0.15+f)+(1.0-color.rgb)*f*0.18,0.0,1.0)*a,a);
}
