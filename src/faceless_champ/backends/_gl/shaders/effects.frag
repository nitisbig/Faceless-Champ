#version 330
uniform sampler2D source;
uniform sampler2D second;
uniform int operation;
uniform vec2 direction;
uniform float weights[129];
uniform int count;
uniform vec4 params;
uniform vec4 tint;
uniform vec4 logical_box;
uniform float progress;
uniform int transition_kind;
uniform float factor;
uniform vec2 output_size;
in vec2 uv;
out vec4 pixel;
vec3 decode(vec3 c) { return mix(pow((c+0.055)/1.055,vec3(2.4)),c/12.92,lessThanEqual(c,vec3(0.04045))); }
vec3 encode(vec3 c) { c=max(c,0.0); return mix(1.055*pow(c,vec3(1.0/2.4))-0.055,c*12.92,lessThanEqual(c,vec3(0.0031308))); }
vec4 straight(vec4 a) { return vec4(a.a>0.0?a.rgb/a.a:vec3(0.0),a.a); }
vec4 premul(vec4 a) { return vec4(a.rgb*a.a,a.a); }
void main() {
    vec4 a=texture(source,uv);
    pixel=a;
    if(operation==1) pixel=vec4(decode(straight(a).rgb)*a.a,a.a);
    else if(operation==2) pixel=vec4(clamp(encode(straight(a).rgb),0.0,1.0)*a.a,a.a);
    else if(operation==3) {
        pixel=vec4(0.0);
        for(int i=-64;i<=64;i++) if(abs(i)<=count)
            pixel+=texture(source,uv+float(i)*direction)*weights[i+64];
    }
    else if(operation==4) pixel=texture(source,uv+vec2(params.x*sin((uv.y*float(textureSize(source,0).y)-logical_box.y)/max(logical_box.w,0.000001)*6.28318530718*params.y+params.z),0.0));
    else if(operation==5) {
        vec4 r=texture(source,uv+vec2(params.x,0.0)),b=texture(source,uv-vec2(params.x,0.0));
        pixel=vec4(r.r,a.g,b.b,max(a.a,max(r.a,b.a)));
    }
    else if(operation==6) pixel=vec4(a.rgb*(1.0+params.x*exp(-0.5*pow(((uv.x*float(textureSize(source,0).x)-logical_box.x)/max(logical_box.z,0.000001)-params.y)/max(params.z,0.000001),2.0))),a.a);
    else if(operation==7) { float alpha=clamp(a.a*params.x*tint.a,0.0,1.0); pixel=vec4(decode(tint.rgb)*alpha,alpha); }
    else if(operation==8) {
        float l=dot(straight(a).rgb,vec3(0.2126,0.7152,0.0722));
        pixel=a*(max(l-params.x,0.0)/max(l,0.00000001));
    }
    else if(operation==9) pixel=a+texture(second,uv)*(1.0-a.a);
    else if(operation==10) {vec4 b=texture(second,uv)*params.x;pixel=vec4(a.rgb+b.rgb,max(a.a,clamp(b.a,0.0,1.0)));}
    else if(operation==18) pixel=a+texture(second,uv)*params.x;
    else if(operation==11) pixel=a*texture(second,uv).a;
    else if(operation==12) {
        vec2 p=uv-params.xy;
        float alpha=(p.x<0.0||p.y<0.0||p.x>1.0||p.y>1.0)?0.0:texture(source,p).a*tint.a;
        pixel=vec4(tint.rgb*alpha,alpha);
    }
    else if(operation==15 || operation==16) {
        if(progress<=0.0) {pixel=a;return;}
        if(progress>=1.0) {pixel=texture(second,uv);return;}
        vec4 aa=straight(a),bb=straight(texture(second,uv));
        float u=progress;
        if(operation==16 && transition_kind==3) {
            aa=vec4(0.0);bb=vec4(0.0);
            float amount=params.x*sin(3.14159265359*progress);
            for(int i=0;i<8;i++) {
                vec2 p=(uv-0.5)/(1.0+amount*float(i)/7.0)+0.5;
                aa+=straight(texture(source,p))/8.0;bb+=straight(texture(second,p))/8.0;
            }
        }
        else if(operation==16) {
            float field=transition_kind==2?dot(aa.rgb,vec3(0.2126,0.7152,0.0722)):uv.x;
            float soft=max(params.x,0.000001);
            u=clamp((progress*(1.0+soft)-field)/soft,0.0,1.0);u=u*u*(3.0-2.0*u);
        }
        pixel=premul(floor(clamp(mix(aa,bb,u),0.0,1.0)*255.0+0.00001)/255.0);
    }
    else if(operation==17) {
        a=vec4(0.0);int n=max(1,int(factor));
        for(int y=0;y<4;y++) for(int x=0;x<4;x++) if(x<n && y<n)
            a+=texture(source,uv+(vec2(x,y)+0.5-float(n)*0.5)/output_size/float(n))/float(n*n);
        pixel=straight(a);
        pixel.a=floor(clamp(a.a,0.0,1.0)*255.0+0.5)/255.0;
        if(pixel.a<=0.0)pixel=vec4(0.0);
    }
}
