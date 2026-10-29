"""Progressive lines keyed to source cues, with stable chapter accumulation."""

from dataclasses import dataclass

from .timing import cue_time


@dataclass(frozen=True)
class Beat:
    cue: int
    expression: str
    color: str = "white"

    @property
    def time(self):
        return cue_time(self.cue)


# Groups persist for the chapter. At most four lines occupy the equation column;
# prior derivation steps move into a compact retained result rail when needed.
BEATS = {
    2: (
        Beat(193, r"m=1700\,\mathrm{kg}"),
        Beat(203, r"W=mg"),
        Beat(217, r"W=1700\times9.81\,\mathrm{N}"),
        Beat(223, r"W\approx16.7\,\mathrm{kN}", "amber"),
    ),
    3: (
        Beat(285, r"N=mg\cos\theta", "blue"),
        Beat(300, r"F_{\parallel}=mg\sin\theta", "amber"),
        Beat(338, r"F_{\max}=\mu N", "green"),
        Beat(354, r"\mu mg\cos\theta\geq mg\sin\theta"),
        Beat(362, r"\tan\theta\leq\mu"),
        Beat(374, r"\mu=1\;\Rightarrow\;\theta_{\max}=45^\circ", "green"),
    ),
    4: (
        Beat(530, r"F_s=\Delta p\,A", "purple"),
        Beat(554, r"F_s=2mg\approx33.4\,\mathrm{kN}", "purple"),
        Beat(574, r"A=2\,\mathrm{m^2}"),
        Beat(577, r"\Delta p=\frac{F_s}{A}"),
        Beat(590, r"\Delta p\approx16.7\,\mathrm{kPa}", "cyan"),
        Beat(638, r"N=mg\cos\theta+F_s", "blue"),
        Beat(681, r"F_{\max}=\mu N\approx33.4\,\mathrm{kN}", "green"),
    ),
    5: (
        Beat(761, r"N=F_s-mg", "blue"),
        Beat(801, r"a_c=\frac{v^2}{R}"),
        Beat(852, r"N+mg-F_s=\frac{mv^2}{R}"),
        Beat(862, r"N=F_s+\frac{mv^2}{R}-mg", "blue"),
        Beat(904, r"\frac{mv^2}{R}=20.4\,\mathrm{kN}"),
        Beat(922, r"N\approx37.1\,\mathrm{kN}", "blue"),
    ),
    6: (
        Beat(1044, r"F=\dot m v_e+(p_e-p_a)A_e"),
        Beat(1061, r"F=\dot m v_{\mathrm{eff}}"),
        Beat(1079, r"F=20\,\mathrm{kN}\,,\quad v_{\mathrm{eff}}=600\,\mathrm{m/s}"),
        Beat(1094, r"\dot m=\frac{F}{v_{\mathrm{eff}}}\approx33.3\,\mathrm{kg/s}", "orange"),
    ),
    7: (
        Beat(1175, r"\boldsymbol{\tau}=\mathbf{r}\times\mathbf{F}", "orange"),
        Beat(1194, r"\tau=I\alpha"),
        Beat(1224, r"I=800\,\mathrm{kg\,m^2}"),
        Beat(1237, r"\theta=\pi\,,\quad T=1.6\,\mathrm{s}"),
        Beat(1289, r"\alpha=\frac{4\theta}{T^2}"),
        Beat(1309, r"\alpha\approx4.91\,\mathrm{rad/s^2}"),
        Beat(1326, r"\tau\approx3.93\,\mathrm{kN\,m}", "orange"),
        Beat(1350, r"d=1.5\,\mathrm{m}"),
        Beat(1356, r"F=\frac{\tau}{d}\approx2.62\,\mathrm{kN}", "orange"),
    ),
    8: (
        Beat(1466, r"m\ddot{\mathbf{r}}=\sum_i\mathbf{F}_i"),
        Beat(
            1474,
            r"\mathbf{I}\dot{\boldsymbol{\omega}}+\boldsymbol{\omega}\times(\mathbf{I}\boldsymbol{\omega})=\boldsymbol{\tau}",
        ),
        Beat(1521, r"\mathbf{w}=\mathbf{B}\mathbf{u}\,,\quad\mathbf{B}\in\mathbb{R}^{6\times10}", "cyan"),
    ),
    9: (
        Beat(1591, r"mgh=\frac{1}{2}mv^2"),
        Beat(1615, r"v=\sqrt{2gh}\approx19.8\,\mathrm{m/s}", "amber"),
        Beat(1647, r"ma_z=T_z-mg"),
        Beat(1688, r"T_z>mg\quad\Rightarrow\quad a_z>0", "orange"),
        Beat(1734, r"v_f^2=v_i^2+2a\,d"),
        Beat(1754, r"a_{\mathrm{net}}\approx g"),
        Beat(1766, r"T_z=m(a_z+g)\approx33.4\,\mathrm{kN}", "orange"),
    ),
}


def visible(chapter, time):
    return tuple(b for b in BEATS.get(chapter, ()) if time >= b.time)
