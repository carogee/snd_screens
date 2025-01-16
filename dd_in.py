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

print("test")
os.system('caput XCS:SND:T1:TH2 -2')
os.system('caput XCS:SND:T4:TH2 -2')
print("dd crystals in")


"""
# Custom class to handle setting PV values
class Insert_CC(PyDMPushButton):
    def __init__(self, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.clicked.connect(self.set_pv_values)
        print("connected pv value")
        self.value=value

    def set_pv_values(self):
        # Set the value for both PVs
        #os.system('caput XCS:SND:T2:TH 16')
        caput('XCS:SND:T2:TH', self.value)
        caput('XCS:SND:T3:TH', self.value)
        print(f"set pv values {self.value}")
        
"""
##obj.set_pv_values()

"""
if __name__ == "__main__":
    app = QApplication(sys.argv)  # Create QApplication instance

    # Create an instance of Insert_CC
    obj = Insert_CC("Click Me")  # First argument is text for the button
    obj.value = 16.1  # Set the value if needed
    obj.set_pv_values()
    obj.show()  # Show the button (or any other QWidget)
    print(obj.value)  # Will print 16.1
    print("done")
    sys.exit(app.exec_())  # Start the application's event loop        
"""
