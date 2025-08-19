import sys
from pydm import PyDMApplication
from pydm.widgets import PyDMPushButton
import os
import numpy as np
from ophyd.signal import EpicsSignalRO
from ophyd.signal import EpicsSignal
from PyQt5 import QtWebEngineWidgets, QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QWidget
from pydm.widgets import PyDMRelatedDisplayButton, PyDMPushButton
from epics import caput

t2th=EpicsSignal("XCS:SND:T2:TH",name="cc1 motor")
t3th=EpicsSignal("XCS:SND:T3:TH",name="cc2 motor")


os.system('caput XCS:SND:T1:TH2 -3')
os.system('caput XCS:SND:T4:TH2 -3')
print("cc crystals in")


