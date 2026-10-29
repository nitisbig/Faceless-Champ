import os
os.environ['MPLCONFIGDIR'] = '/tmp/mpl_cache'
from matplotlib.mathtext import MathTextParser

parser = MathTextParser('path')

terms = [
    r'$A$',
    r'$B$',
    r'$C$',
    r'$\mathrm{Gear}\ A$',
    r'$\mathrm{Gear}\ B$',
    r'$\mathrm{Gear}\ C$',
    r'$1\ \mathrm{Turn}$',
    r'$2\ \mathrm{Turns}$',
    r'$\frac{dB}{dA}$',
    r'$=$',
    r'$2$',
    r'$(\times 2)$',
    r'$\mathrm{Rate} = \times 2$',
    r'$\omega_B = 2\omega_A$'
]

for t in terms:
    try:
        parser.parse(t, dpi=72)
        print('OK:', t)
    except Exception as e:
        print('FAIL:', t, '-->', e)
