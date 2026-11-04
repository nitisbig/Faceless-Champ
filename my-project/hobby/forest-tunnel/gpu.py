"""GPU renderer for the forest tunnel: path-space point clouds, speed streaks and a world curl.

Points are stored in path coordinates (s, u, v). The vertex shader optionally curls the
cross-section (u, v) about an axis for everything beyond ``curl_s0`` (the world rolls into a
tube), then maps it through two path textures (centre and lateral vectors) into world space.
Light is computed in path space from a light that travels ahead of the camera, so the path and
canopy ahead glow while the near world stays dark.

Passes per frame: occluder depth prepass, additive points (square sprites for near motes), speed
streaks as GL lines from last frame's camera to this one, a quarter-res smoke pass, then bloom,
filmic tonemap and dither.
"""

from __future__ import annotations

import moderngl
import numpy as np

COMMON = """
uniform sampler2D path_c;
uniform sampler2D path_l;
uniform vec2 s_range;
uniform vec2 curl_axis;
uniform float curl_len;
uniform vec3 light_suv;
uniform float light_r, light_k, ambient;
uniform vec3 light_col;
uniform float t;
uniform int kind;
uniform float fog, gain, unlit;
uniform vec2 res;

float hash3(vec3 p) { return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }

vec3 animate(vec3 suv, float tt) {
    if (kind == 1) {  // motes drift
        float h = hash3(suv);
        suv += vec3(0.25 * sin(tt * 0.5 + h * 6.28), 0.2 * sin(tt * 0.37 + h * 11.0), 0.15 * sin(tt * 0.6 + h * 17.0));
    }
    return suv;
}

vec3 warp(vec3 suv, float amt, float s0) {
    vec2 uv = suv.yz;
    float d = suv.x - s0;
    if (amt > 0.0 && d > 0.0) {
        float k = smoothstep(0.0, curl_len, d);
        float th = amt * 5.6 * pow(k, 1.25);
        vec2 rel = uv - curl_axis;
        float c = cos(th), sn = sin(th);
        uv = curl_axis + vec2(rel.x * c - rel.y * sn, rel.x * sn + rel.y * c);
    }
    float tc = (suv.x - s_range.x) / (s_range.y - s_range.x);
    vec3 C = texture(path_c, vec2(tc, 0.5)).xyz;
    vec3 L = texture(path_l, vec2(tc, 0.5)).xyz;
    return C + L * uv.x + vec3(0.0, uv.y, 0.0);
}

vec3 shade(vec3 suv, vec3 alb) {
    if (unlit > 0.5) return alb;
    vec3 d = (suv - light_suv) * vec3(1.0, 1.0, 1.3);
    float l = light_k / (1.0 + pow(length(d) / light_r, 2.2));
    return alb * (ambient + l * light_col);
}

vec3 project(vec3 p, vec3 pos, vec3 right, vec3 up, vec3 fwd, float focal) {
    vec3 d = p - pos;
    float z = dot(d, fwd);
    return vec3(focal * dot(d, right) / max(z, 1e-3), focal * dot(d, up) / max(z, 1e-3), z);
}

float log_depth(float z) { return clamp(log(max(z, 0.05) / 0.05) / log(20000.0), 0.0, 1.0) * 2.0 - 1.0; }
"""

POINT_VS = """
#version 330
in vec3 in_suv;
in vec3 in_alb;
in float in_size;
uniform vec3 cam_pos, cam_right, cam_up, cam_fwd;
uniform float focal, curl_amt, curl_s0;
uniform float depth_pass, occ_size;
out vec3 v_col;
""" + COMMON + """
void main() {
    vec3 suv = animate(in_suv, t);
    vec3 q = project(warp(suv, curl_amt, curl_s0), cam_pos, cam_right, cam_up, cam_fwd, focal);
    if (q.z < 0.1) { gl_Position = vec4(3.0, 3.0, 3.0, 1.0); gl_PointSize = 1.0; v_col = vec3(0.0); return; }
    float zd = depth_pass > 0.5 ? q.z * 1.02 + 0.15 : q.z;
    gl_Position = vec4(q.x / (res.x * 0.5), q.y / (res.y * 0.5), log_depth(zd), 1.0);
    float fade = pow(clamp((q.z - 0.1) / 0.9, 0.0, 1.0), 2.0) * exp(-q.z / fog);
    v_col = shade(in_suv, in_alb) * fade * gain;
    float size = in_size > 0.0 ? in_size * focal / q.z : 0.0;
    // near occluders stay small so close foliage reads as a sparse scan, not a black wall
    if (depth_pass > 0.5) size = clamp(occ_size * focal / q.z, 1.0, 1.5 * res.x / 1280.0 + 1.0);
    gl_PointSize = clamp(size, 1.0, 8.0 * res.x / 1280.0 + 1.0);
}
"""

LINE_VS = """
#version 330
in vec3 in_suv;
in vec3 in_alb;
in float in_end;
uniform vec3 cam_pos, cam_right, cam_up, cam_fwd;
uniform vec3 pcam_pos, pcam_right, pcam_up, pcam_fwd;
uniform float focal, pfocal, curl_amt, curl_s0, pcurl_amt, pcurl_s0, t_prev;
out vec3 v_col;
""" + COMMON + """
void main() {
    vec3 a = project(warp(animate(in_suv, t), curl_amt, curl_s0), cam_pos, cam_right, cam_up, cam_fwd, focal);
    vec3 b = project(warp(animate(in_suv, t_prev), pcurl_amt, pcurl_s0), pcam_pos, pcam_right, pcam_up, pcam_fwd, pfocal);
    if (a.z < 0.25 || b.z < 0.25) { gl_Position = vec4(3.0, 3.0, 3.0, 1.0); v_col = vec3(0.0); return; }
    vec3 q = in_end > 0.5 ? b : a;
    gl_Position = vec4(q.x / (res.x * 0.5), q.y / (res.y * 0.5), log_depth(a.z), 1.0);
    float len = length(a.xy - b.xy);
    float fade = pow(clamp((a.z - 0.25) / 1.0, 0.0, 1.0), 2.0) * exp(-a.z / fog) * smoothstep(2.0, 8.0, len);
    v_col = shade(in_suv, in_alb) * fade * gain * (in_end > 0.5 ? 0.05 : 1.0);
}
"""

FS = """
#version 330
in vec3 v_col;
out vec4 frag;
void main() { frag = vec4(v_col, 1.0); }
"""

QUAD_VS = """
#version 330
in vec2 in_xy;
out vec2 uv;
void main() { uv = in_xy * 0.5 + 0.5; gl_Position = vec4(in_xy, 0.0, 1.0); }
"""

DOWN_FS = """
#version 330
uniform sampler2D src;
uniform int factor;
in vec2 uv;
out vec4 frag;
void main() {
    ivec2 base = ivec2(gl_FragCoord.xy) * factor;
    vec3 acc = vec3(0.0);
    for (int y = 0; y < factor; y++) for (int x = 0; x < factor; x++) acc += texelFetch(src, base + ivec2(x, y), 0).rgb;
    frag = vec4(acc / float(factor * factor), 1.0);
}
"""

BLUR_FS = """
#version 330
uniform sampler2D src;
uniform vec2 step_uv;
uniform float sigma;
in vec2 uv;
out vec4 frag;
void main() {
    int r = int(ceil(sigma * 2.5));
    vec3 acc = vec3(0.0);
    float wsum = 0.0;
    for (int i = -r; i <= r; i++) {
        float w = exp(-0.5 * float(i * i) / (sigma * sigma));
        acc += w * texture(src, uv + step_uv * float(i)).rgb;
        wsum += w;
    }
    frag = vec4(acc / wsum, 1.0);
}
"""

COMP_FS = """
#version 330
uniform sampler2D sharp;
uniform sampler2D soft;
uniform sampler2D bloom_a;
uniform sampler2D bloom_b;
uniform float k_soft, k_bloom, exposure;
uniform vec3 bg;
uniform float seed;
in vec2 uv;
out vec4 frag;
float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233)) + seed) * 43758.5453); }
void main() {
    vec3 c = texture(sharp, uv).rgb + texture(soft, uv).rgb * k_soft;
    c += (texture(bloom_a, uv).rgb * 0.8 + texture(bloom_b, uv).rgb * 0.5) * k_bloom;
    c = 1.0 - exp(-c * exposure);
    c = bg + (1.0 - bg) * clamp(c, 0.0, 1.0);
    c += (hash(gl_FragCoord.xy) - 0.5) / 255.0;
    frag = vec4(c, 1.0);
}
"""


class TunnelRenderer:
    def __init__(self, layers: dict, path_s, path_c, path_l, width: int, height: int):
        self.w, self.h = width, height
        self.lw, self.lh = max(2, width // 4), max(2, height // 4)
        self.ctx = ctx = moderngl.create_standalone_context(require=330)
        self.prog = ctx.program(vertex_shader=POINT_VS, fragment_shader=FS)
        self.lprog = ctx.program(vertex_shader=LINE_VS, fragment_shader=FS)
        self.s_range = (float(path_s[0]), float(path_s[-1]))

        self.path_tex = []
        for arr in (path_c, path_l):
            tex = ctx.texture((len(arr), 1), 3, data=np.ascontiguousarray(arr, "f4").tobytes(), dtype="f4")
            tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            tex.repeat_x = tex.repeat_y = False
            self.path_tex.append(tex)

        self.layers = []
        for name, L in layers.items():
            data = np.concatenate([L["suv"], L["alb"], L["size"][:, None]], 1).astype("f4")
            vao = ctx.vertex_array(self.prog, [(ctx.buffer(data.tobytes()), "3f 3f 1f", "in_suv", "in_alb", "in_size")])
            lvao = None
            if L.get("streak"):
                n = len(data)
                ldata = np.empty((n * 2, 7), "f4")
                ldata[0::2, :6] = data[:, :6]
                ldata[1::2, :6] = data[:, :6]
                ldata[0::2, 6] = 0.0
                ldata[1::2, 6] = 1.0
                lvao = ctx.vertex_array(self.lprog, [(ctx.buffer(ldata.tobytes()), "3f 3f 1f", "in_suv", "in_alb", "in_end")])
            self.layers.append((name, L, vao, lvao, len(data)))

        def target(w, h, depth=True):
            tex = ctx.texture((w, h), 4, dtype="f4")
            tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            tex.repeat_x = tex.repeat_y = False
            dep = ctx.depth_texture((w, h)) if depth else None
            return tex, dep, ctx.framebuffer([tex], dep)

        self.sharp, self.depth, self.fbo_sharp = target(width, height)
        self.smoke, self.depth_low, self.fbo_smoke = target(self.lw, self.lh)
        self.lows = {k: target(self.lw, self.lh, depth=False) for k in ("down", "tmp", "soft", "bloom_a", "bloom_b")}
        self.out = ctx.texture((width, height), 4, dtype="f1")
        self.fbo_out = ctx.framebuffer([self.out])
        quad = ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], "f4").tobytes())
        self.passes = {}
        for key, fs in (("down", DOWN_FS), ("blur", BLUR_FS), ("comp", COMP_FS)):
            prog = ctx.program(vertex_shader=QUAD_VS, fragment_shader=fs)
            self.passes[key] = (prog, ctx.vertex_array(prog, [(quad, "2f", "in_xy")]))

    @staticmethod
    def _set(prog, **values):
        for k, v in values.items():
            if k in prog:
                prog[k].value = tuple(float(x) for x in v) if isinstance(v, (tuple, list, np.ndarray)) else v

    def _quad(self, key, fbo, **uniforms):
        prog, vao = self.passes[key]
        textures = {k: v for k, v in uniforms.items() if isinstance(v, moderngl.Texture)}
        for i, (name, tex) in enumerate(textures.items()):
            tex.use(location=i)
            if name in prog:
                prog[name].value = i
        self._set(prog, **{k: v for k, v in uniforms.items() if k not in textures})
        fbo.use()
        vao.render(moderngl.TRIANGLE_STRIP)

    def _blur(self, src, dst, sigma):
        tmp_tex, _, tmp_fbo = self.lows["tmp"]
        self._quad("blur", tmp_fbo, src=src, step_uv=(1.0 / self.lw, 0.0), sigma=sigma)
        self._quad("blur", dst[2], src=tmp_tex, step_uv=(0.0, 1.0 / self.lh), sigma=sigma)

    def _draw(self, size, uni, pass_kind):
        w, h = size
        kres = (1280.0 / self.w) ** 2
        for prog in (self.prog, self.lprog):
            self.path_tex[0].use(location=0)
            self.path_tex[1].use(location=1)
            self._set(prog, path_c=0, path_l=1, s_range=self.s_range, res=(w, h),
                      focal=uni["focal"] * w, pfocal=uni["pfocal"] * w,
                      **{k: v for k, v in uni.items() if k not in ("focal", "pfocal")})
        for name, L, vao, lvao, n in self.layers:
            if pass_kind == "depth":
                occ = float(L.get("occ", 0.0))
                if occ <= 0:
                    continue
                self._set(self.prog, kind=int(L.get("kind", 0)), fog=1e9, gain=0.0, unlit=0.0, depth_pass=1.0, occ_size=occ)
                vao.render(moderngl.POINTS, vertices=n)
                continue
            weight = float(L.get(pass_kind, 1.0 if pass_kind == "sharp" else 0.0)) * float(L.get("gain", 1.0)) * kres
            if weight <= 0:
                continue
            common = dict(kind=int(L.get("kind", 0)), fog=float(L.get("fog", 45.0)), gain=weight,
                          unlit=1.0 if L.get("unlit") else 0.0)
            self._set(self.prog, depth_pass=0.0, occ_size=0.0, **common)
            vao.render(moderngl.POINTS, vertices=n)
            if lvao is not None and pass_kind == "sharp":
                self._set(self.lprog, **dict(common, gain=weight * float(L.get("streak_gain", 1.0))))
                lvao.render(moderngl.LINES, vertices=2 * n)

    def _scene_pass(self, fbo, size, uni, kind):
        ctx = self.ctx
        fbo.use()
        fbo.depth_mask = True
        fbo.color_mask = (True, True, True, True)
        fbo.clear(0.0, 0.0, 0.0, 0.0, depth=1.0)
        ctx.enable(moderngl.DEPTH_TEST | moderngl.PROGRAM_POINT_SIZE)
        ctx.disable(moderngl.BLEND)
        ctx.depth_func = "<"
        fbo.color_mask = (False, False, False, False)
        self._draw(size, uni, "depth")
        fbo.color_mask = (True, True, True, True)
        fbo.depth_mask = False
        ctx.depth_func = "<="
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = (moderngl.ONE, moderngl.ONE)
        self._draw(size, uni, kind)
        ctx.disable(moderngl.DEPTH_TEST | moderngl.BLEND)
        fbo.depth_mask = True

    def frame(self, uni, *, k_soft, k_bloom, exposure, bg, seed):
        self._scene_pass(self.fbo_sharp, (self.w, self.h), uni, "sharp")
        self._scene_pass(self.fbo_smoke, (self.lw, self.lh), uni, "smoke")
        down = self.lows["down"]
        self._quad("down", down[2], src=self.sharp, factor=self.w // self.lw)
        q = self.lw / 320
        self._blur(self.smoke, self.lows["soft"], 1.6 * q)
        self._blur(down[0], self.lows["bloom_a"], 1.5 * q)
        self._blur(down[0], self.lows["bloom_b"], 7.0 * q)
        self._quad("comp", self.fbo_out, sharp=self.sharp, soft=self.lows["soft"][0], bloom_a=self.lows["bloom_a"][0],
                   bloom_b=self.lows["bloom_b"][0], k_soft=k_soft, k_bloom=k_bloom, exposure=exposure, bg=bg, seed=seed)
        img = np.frombuffer(self.fbo_out.read(components=3, dtype="f1"), np.uint8).reshape(self.h, self.w, 3)
        return img[::-1]
