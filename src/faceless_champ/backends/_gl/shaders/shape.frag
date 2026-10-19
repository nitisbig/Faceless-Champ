#version 330
uniform vec2 extent;
uniform float radius;
uniform int ellipse;
uniform vec4 fill_color;
uniform vec4 stroke_color;
uniform float stroke_width;
uniform float opacity;
uniform int paint_kind;
uniform int stop_count;
uniform vec4 colors[64];
uniform float stops[64];
uniform vec4 gradient;
in vec2 local;
out vec4 pixel;
vec4 paint() {
    if(paint_kind==0)return fill_color;
    float t;
    if(paint_kind==1) {
        float span=dot(abs(gradient.xy),extent);
        t=dot(local,gradient.xy)/max(span,0.00001)+0.5;
    } else t=length(local-(gradient.xy-0.5)*extent)/max(gradient.z*min(extent.x,extent.y),0.00001);
    t=clamp(t,0.0,1.0);
    vec4 c=colors[0];
    for(int i=1;i<64;i++)if(i<stop_count) {
        if(t>=stops[i])c=colors[i];
        else if(t>stops[i-1]) {c=mix(colors[i-1],colors[i],(t-stops[i-1])/(stops[i]-stops[i-1]));break;}
    }
    return c;
}
void main() {
    vec2 half_size=extent*0.5;
    vec2 q=abs(local)-half_size+radius;
    float d=length(max(q,0.0))+min(max(q.x,q.y),0.0)-radius;
    if(ellipse==1)d=(length(local/max(half_size,vec2(0.0001)))-1.0)*min(half_size.x,half_size.y);
    float aa=max(fwidth(d),0.0001);
    float inside=clamp(0.5-d/aa,0.0,1.0);
    float edge=stroke_width>0.0?clamp(0.5-(abs(d)-stroke_width*0.5)/aa,0.0,1.0):0.0;
    vec4 f=paint()*inside,s=stroke_color*edge;
    vec4 a=s+f*(1.0-s.a);
    float alpha=opacity==1.0?a.a:floor(a.a*opacity*255.0+0.5)/255.0;
    pixel=vec4(a.rgb*alpha/max(a.a,0.00000001),alpha);
}
