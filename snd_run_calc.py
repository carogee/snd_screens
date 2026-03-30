#from snd_calc import *

import sys
sys.path.insert(1,'/reg/g/pcds/pyps/apps/hutch-python/xcs/xcs')
import numpy as np
import matplotlib.pyplot as plt
from ophyd import EpicsSignal
from pcdsdevices import analog_signals
from time import sleep

from beamline import show_cc, show_delay, show_both
from beamline import snd_correlation

#from snd_calc import show_cc, show_delay, show_both
#from snd_calc import snd_correlation

snd_correlation()


#def update_ratio_calculation():
#    coff_cc_value, coff_dd_value, ratio_value = snd_correlation(nshots=240,do_ch=6)
#    return coff_cc_value, coff_dd_value, ratio_value
