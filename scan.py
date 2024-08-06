##source /cds/group/pcds/pyps/conda/dev_conda before running script                       
from subprocess import check_output

import logging
import json
import sys
import time
import os

from ophyd import EpicsSignalRO
from ophyd import EpicsSignal
from bluesky import RunEngine
from bluesky.plans import scan, list_scan, count
#from bluesky.plan_stubs import abs_set, trigger_and_read                                 
from ophyd import Component as Cpt
from ophyd import Device
from ophyd.sim import det, motor #simulation motors/detectors                             


#callback to show live plots/tables                                                                     
from bluesky.callbacks.best_effort import BestEffortCallback
bec = BestEffortCallback()
RE = RunEngine({})
RE.subscribe(bec)

from bluesky.utils import install_kicker

#practice scan with simulated motor                                                                     

dets = [det]
#RE(scan([det], motor, 1,5,5))                                                                          
RE(count([det], num=5))

print("Done")
