import sys
import os
from os import path
from pydm import Display
from PyQt5 import QtWidgets, uic
from bluesky import RunEngine
RE = RunEngine({})
from bluesky.plans import scan
from ophyd.signal import EpicsSignal
from databroker import Broker
from pydm import PyDMApplication

from pydm.widgets.channel import PyDMChannel
#from scan_theta import anglex1, anglex2, anglex3, anglex4, anglecc1, anglecc2 
from pydm.data_plugins.local_plugin import LocalPlugin
from scan_theta import AngleX1Align, AngleX2Align, AngleX3Align, AngleX4Align, AngleCC1Align, AngleCC2Align
from pydm.widgets.pushbutton import PyDMPushButton
from PyQt5.QtCore import QCoreApplication, Qt, QTimer
from PyQt5 import QtWebEngineWidgets, QtCore, QtWidgets
from pydm.widgets.channel import PyDMChannel
from pydm.widgets.scatterplot import PyDMScatterPlot
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QWidget
from PyQt5.QtWidgets import QMainWindow, QWidget
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.plan_stubs import stop
from epics import caput
from collections import deque
import numpy as np

#db = Broker.named('temp')
bec = BestEffortCallback()
RE.subscribe(bec)

from bluesky.utils import install_kicker
#install_kicker()


current_directory = os.getcwd()
print("current directory", current_directory)
file_path=os.path.join(current_directory, 'motors_screen.ui')
print("file path", file_path)


# Class for displaying the average of last 120 values from a PV
class AvgSignal:
    def __init__(self, signal, averages=120, name=''):
        self.signal = signal
        self.averages = averages
        self.history = []  # To hold the history of values

    def get(self):
        # Get the current value from EPICS
        value = self.signal.value
        # Maintain history for averaging
        self.history.append(value)
        if len(self.history) > self.averages:
            self.history.pop(0)  # Keep only the last 'averages' values

        return np.mean(self.history) if self.history else 0


class MyDevice:
    def __init__(self):
        ch12 = EpicsSignal('XCS:SND:DIO:AMPL_12', name='ch12', auto_monitor=True)
        dcc = EpicsSignal('XCS:SND:DIO:AMPL_8', name='dcc_signal', auto_monitor=True)
        # Initialize the EpicsSignal                                                                                 print("initializing epics signal")                       
        self.ch12 = AvgSignal(signal=ch12, averages=120, name='ch12')
        self.dcc_signal = AvgSignal(signal=dcc, averages=120, name='dcc_signal')


class MyDisplay(Display):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.my_device = MyDevice()  # Create an instance of MyDevice
        uic.loadUi('/cds/home/c/cagee/SND/motors_screen.ui', self)
        #uic.loadUi(file_path, self)

        #PydmRelatedDisplay buttons connect to custom functions:                                           
        self.X1.clicked.connect(self.scan_openx1)
        self.X2.clicked.connect(self.scan_openx2)
        self.X3.clicked.connect(self.scan_openx3)
        self.X4.clicked.connect(self.scan_openx4)
        self.CC1.clicked.connect(self.scan_opencc1)
        self.CC2.clicked.connect(self.scan_opencc2)

        # Create a QLabel to display the average value
        self.average_label = QtWidgets.QLabel(self)  # Use QLabel from QtWidgets
        self.average_label.setGeometry(223, 80, 200, 50)  # Set position and size
        self.average_label.setText("Average: 0.0")

        # Set up a timer to update the average value every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_average)
        self.timer.start(1000)  # Update every second
        print("initialized timer")

    def update_average(self):
        # Get the averaged value and update the label
        averaged_value_dcc = self.my_device.dcc_signal.get()
        averaged_value_ch12 = self.my_device.ch12.get()
        averaged_ratio = averaged_value_ch12/averaged_value_dcc
        self.average_label.setText(f"{averaged_ratio:.2f}")

    def scan_openx1(self):
        self.angle_x1_scan=AngleX1Align(self)
        self.startButton=AngleX1Align(self)
        self.angle_x1_scan.setWindowFlags(QtCore.Qt.Window)
        self.angle_x1_scan.show()
        self.angle_x1_scan.start_scan()
       
    def scan_openx2(self):
        self.angle_x2_scan=AngleX2Align(self)
        self.startButton=AngleX2Align(self)
        self.angle_x2_scan.setWindowFlags(QtCore.Qt.Window)
        self.angle_x2_scan.show()
        self.angle_x2_scan.start_scan()

    def scan_openx3(self):
        self.angle_x3_scan=AngleX3Align(self)
        self.startButton=AngleX3Align(self)
        self.angle_x3_scan.setWindowFlags(QtCore.Qt.Window)
        self.angle_x3_scan.show()
        self.angle_x3_scan.start_scan()

    def scan_openx4(self):
        self.angle_x4_scan=AngleX4Align(self)
        self.startButton=AngleX4Align(self)
        self.angle_x4_scan.setWindowFlags(QtCore.Qt.Window)
        self.angle_x4_scan.show()
        self.angle_x4_scan.start_scan()

    def scan_opencc1(self):
        self.angle_cc1_scan=AngleCC1Align(self)
        self.startButton=AngleCC1Align(self)
        self.angle_cc1_scan.setWindowFlags(QtCore.Qt.Window)
        self.angle_cc1_scan.show()
        self.angle_cc1_scan.start_scan()

    def scan_opencc2(self):
        self.angle_cc2_scan=AngleCC2Align(self)
        self.startButton=AngleCC2Align(self)
        self.angle_cc2_scan.setWindowFlags(QtCore.Qt.Window)
        self.angle_cc2_scan.show()
        self.angle_cc2_scan.start_scan()

    def ui_filename(self):
        return '/cds/home/c/cagee/SND/motors_screen.ui'

    def ui_filepath(self):
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())
   
 
if __name__=='__main__':
    from pydm import PyDMApplication
    app = QtWidgets.QApplication(sys.argv)
    display = MyDisplay()
    display.show()
    sys.exit(app.exec_())
