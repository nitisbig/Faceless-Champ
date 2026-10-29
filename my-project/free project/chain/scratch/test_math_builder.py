import os
os.environ['MPLCONFIGDIR'] = '/tmp/mpl_cache'
from matplotlib.mathtext import MathTextParser

parser = MathTextParser('path')

test_strings = [
    r'$\frac{ds}{dt}$',
    r'$=$',
    r'$\frac{ds}{d\theta}$',
    r'$\cdot$',
    r'$\frac{d\theta}{dt}$',
    r'$\Delta B$',
    r'$\approx$',
    r'$\frac{dB}{dr}$',
    r'$\Delta r$',
    r'$\frac{dA}{dC}$',
    r'$\frac{dA}{dB}$',
    r'$\frac{dB}{dC}$',
    r'$\frac{dy}{dx}$',
    r'$\lim_{\Delta x \to 0}$',
    r'$\frac{\Delta y}{\Delta x}$',
    r'$2x$',
    r'$\cos(x^2)$',
    r'$\frac{\partial L}{\partial w}$',
    r'$\frac{\partial L}{\partial a}$',
    r'$\frac{\partial a}{\partial z}$',
    r'$\frac{\partial z}{\partial w}$',
    r'$\Delta r = +0.25\%$',
    r'$\vec{v} = \frac{ds}{dt}$',
    r'$\theta$',
    r'$h$',
    r'$t$',
    r'$B$',
    r'$\Delta B$',
]

for s in test_strings:
    try:
        parser.parse(s, dpi=72)
        print('OK:', s)
    except Exception as e:
        print('FAILED:', s, '-->', e)
