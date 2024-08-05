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


#Write a practice scan with the simulated motor                                                       



print("Done")
