"""The editorial content: change an equation here to adapt the example."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EquationSpec:
    number: int
    title: str
    category: str
    expression: str
    description: str
    example: str
    icon: str
    accent_role: str
    diagram: str

    def accent(self, scheme):
        return scheme.color(self.accent_role)

    def color_map(self, scheme):
        return {symbol: scheme.color(role) for symbol, role in SYMBOL_ROLES[self.number].items()}


# A symbol's color is repeated in its graph, labels, and worked example.
SYMBOL_ROLES = {
    1: {"a": "primary", "b": "secondary", "c": "tertiary"},
    2: {"x": "highlight", "a": "primary", "b": "secondary", "c": "tertiary"},
    3: {"m": "tertiary", "x": "primary", "y": "secondary"},
    4: {"A": "secondary", "P": "primary", "r": "tertiary", "t": "highlight"},
    5: {"f": "primary", r"\prime": "secondary", "x": "tertiary", "h": "highlight"},
    6: {"f": "primary", "F": "highlight", "a": "secondary", "b": "tertiary", "x": "primary"},
    7: {"F": "primary", "m": "secondary", "a": "tertiary"},
    8: {"P": "highlight", "A": "primary", "B": "secondary"},
    9: {"f": "primary", r"\mu": "secondary", r"\sigma": "tertiary"},
    10: {"f": "tertiary", "t": "primary", r"\nu": "secondary", "i": "highlight"},
}


EQUATIONS = (
    EquationSpec(
        1,
        "Pythagorean theorem",
        "GEOMETRY",
        r"a^2+b^2=c^2",
        "Find distance in a right triangle.",
        r"3^2+4^2=5^2",
        "square_foot",
        "tertiary",
        "triangle",
    ),
    EquationSpec(
        2,
        "Quadratic formula",
        "ALGEBRA",
        r"x=\frac{-b\pm\sqrt{b^2-4ac}}{2a}",
        "Find the roots of any quadratic; a ≠ 0.",
        r"x^2-5x+6=0\quad\Rightarrow\quad x=2,\,3",
        "calculate",
        "highlight",
        "quadratic",
    ),
    EquationSpec(
        3,
        "Slope of a line",
        "COORDINATES",
        r"m=\frac{y_2-y_1}{x_2-x_1}",
        "Measure steepness; x2 ≠ x1.",
        r"\frac{5-1}{3-1}=2",
        "trending_up",
        "primary",
        "slope",
    ),
    EquationSpec(
        4,
        "Compound interest",
        "GROWTH",
        r"A=P\left(1+\frac{r}{n}\right)^{nt}",
        "Let interest earn more interest.",
        r"1000(1.05)^2=1102.50",
        "payments",
        "secondary",
        "growth",
    ),
    EquationSpec(
        5,
        "The derivative",
        "CALCULUS",
        r"f'(x)=\lim_{h\to0}\frac{f(x+h)-f(x)}{h}",
        "Find the instantaneous rate of change.",
        r"f(x)=x^2\quad\Rightarrow\quad f'(3)=6",
        "show_chart",
        "tertiary",
        "derivative",
    ),
    EquationSpec(
        6,
        "Fundamental theorem",
        "CALCULUS",
        r"\int_a^b f(x)\,dx=F(b)-F(a)",
        "Turn accumulation into subtraction; F' = f.",
        r"\int_0^2 x\,dx=2",
        "area_chart",
        "secondary",
        "integral",
    ),
    EquationSpec(
        7,
        "Newton’s second law",
        "PHYSICS",
        r"\sum F=ma",
        "Net force changes motion; constant mass.",
        r"2\,\mathrm{kg}\times3\,\mathrm{m/s^2}=6\,\mathrm{N}",
        "bolt",
        "primary",
        "force",
    ),
    EquationSpec(
        8,
        "Bayes’ theorem",
        "PROBABILITY",
        r"P(A\mid B)=\frac{P(B\mid A)P(A)}{P(B)}",
        "Update a belief with evidence; P(B) > 0.",
        r"\frac{0.8\times0.1}{0.2}=0.4",
        "device_hub",
        "highlight",
        "bayes",
    ),
    EquationSpec(
        9,
        "Normal distribution",
        "STATISTICS",
        r"f(x)=\frac{1}{\sigma\sqrt{2\pi}}e^{-\frac{(x-\mu)^2}{2\sigma^2}}",
        "Model variation around a mean.\nThe mean sets the center; standard deviation > 0.",
        r"P(\mu-\sigma<X<\mu+\sigma)\approx68.3\%",
        "analytics",
        "secondary",
        "normal",
    ),
    EquationSpec(
        10,
        "Fourier transform",
        "SIGNALS",
        r"\hat f(\nu)=\int_{-\infty}^{\infty}f(t)e^{-2\pi i\nu t}\,dt",
        "Reveal the frequencies inside a signal.\nUsed in audio, imaging, and communication.",
        r"\mathrm{signal}\quad\longleftrightarrow\quad\mathrm{frequencies}",
        "graphic_eq",
        "tertiary",
        "fourier",
    ),
)
