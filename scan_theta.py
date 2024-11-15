##source /cds/group/pcds/pyps/conda/dev_conda before running script
#scan_theta.py referenced for snd_gui.py
from subprocess import check_output

import logging
import json
import sys
import time
import os

from ophyd.signal import EpicsSignalRO
from ophyd.signal import EpicsSignal
from bluesky import RunEngine
from bluesky.plans import scan, list_scan, count
from bluesky.plan_stubs import abs_set, trigger_and_read, stop
from ophyd import Component as Cpt
from ophyd import Device
from ophyd.sim import det, det1, det2, det3, det4, motor, motor1, motor2, motor3 #simulation motors/detectors

#import relevant pydm/qt 
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5 import QtWebEngineWidgets, QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QWidget

from pydm.widgets import PyDMRelatedDisplayButton, PyDMPushButton

d12=EpicsSignalRO("XCS:SND:DIO:AMPL_12",name="diode 12") #define PV
d15=EpicsSignalRO("XCS:SND:DIO:AMPL_15",name="diode 15")
d8=EpicsSignalRO("XCS:SND:DIO:AMPL_8",name="diode 8")
d9=EpicsSignalRO("XCS:SND:DIO:AMPL_9",name="diode 9")
d11=EpicsSignalRO("XCS:SND:DIO:AMPL_11",name="diode 11")
d10=EpicsSignalRO("XCS:SND:DIO:AMPL_10",name="diode 10")
d15=EpicsSignalRO("XCS:SND:DIO:AMPL_15",name="diode 15")
d14=EpicsSignalRO("XCS:SND:DIO:AMPL_14",name="diode 14")
d13=EpicsSignalRO("XCS:SND:DIO:AMPL_13",name='diode 13')

#angle motors for each button
t1th1=EpicsSignal("XCS:SND:T1:TH1",name="x1 motor")
t1th2=EpicsSignal("XCS:SND:T1:TH2",name="x2 motor")
t2th=EpicsSignal("XCS:SND:T2:TH",name="cc1 motor")
t3th=EpicsSignal("XCS:SND:T3:TH",name="cc2 motor")
t4th1=EpicsSignal("XCS:SND:T4:TH1",name="x4 motor")
t4th2=EpicsSignal("XCS:SND:T4:TH2",name="x3 motor") #X3 align

RE=RunEngine({})
from bluesky.callbacks.best_effort import BestEffortCallback
bec=BestEffortCallback()
RE.subscribe(bec)
from bluesky.utils import install_kicker

 
#        Classes for each angle control ui screen with start, end, number of steps inputs
#functions to call in the classes inside each class
# each class for the 6 different buttons/motors
# classes for pop up Buttons in snd_gui.py to call on: 

class AngleX1Align(PyDMPushButton):
	def __init__(self,parent=None):
		super(AngleX1Align,self).__init__(parent)
		uic.loadUi("/cds/home/c/cagee/SND/angle_x1.ui",self)
		self.startButton.clicked.connect(self.start_scan)
		self.stopButton.clicked.connect(self.stop_scan)	
	def anglex1(self):

		start_angle=float(self.startLineEdit.text())
		end_angle = float(self.stopLineEdit.text())
		steps = float(self.stepLineEdit.text())

#line to input PVs: scans over motor and upstream diode
		yield from scan([d11],t1th1,start_angle,end_angle,steps)

	def start_scan(self):
                #  Read values from UI and perform a Bluesky scan
	
		RE(self.anglex1())

		print("scanning motor X1...")

	def stop_scan(self):
		RE.stop()
		print("Stopped scanning motor X1")
	def ui_filename(self):
		return '/cds/home/c/cagee/SND/angle_x1.ui'
class AngleX2Align(PyDMPushButton):
	def __init__(self,parent=None):
		super(AngleX2Align,self).__init__(parent)
		uic.loadUi("/cds/home/c/cagee/SND/angle_x2.ui",self)	
		self.startButton.clicked.connect(self.start_scan)
		self.stopButton.clicked.connect(self.stop_scan)	
	def anglex2(self):
		start_angle=float(self.startLineEdit.text())
		end_angle=float(self.stopLineEdit.text())
		steps=float(self.stepLineEdit.text())
		yield from scan([d12],t1th2,start_angle,end_angle,steps)
	def start_scan(self):
                # Read values and perform a Bluesky scan
		
		RE(self.anglex2())
		print("scanning motor X2...")
	def stop_scan(self):
		RE.stop()
		print("Stopped scanning motor X2")
	def ui_filename(self):
		return '/cds/home/c/cagee/SND/angle_x2.ui'
class AngleX3Align(PyDMPushButton):
	def __init__(self,parent=None):
		super(AngleX3Align,self).__init__(parent)
		uic.loadUi("/cds/home/c/cagee/SND/angle_x3.ui",self)
		self.startButton.clicked.connect(self.start_scan)
		self.stopButton.clicked.connect(self.stop_scan)
	def anglex3(self):
                # Example: Read values from UI and perform a Bluesky scan
		start_angle = float(self.startLineEdit.text())
		end_angle = float(self.stopLineEdit.text())
		steps = float(self.stepLineEdit.text())
		yield from scan([d15],t4th2,start_angle,end_angle,steps)
	def start_scan(self):
		RE(self.anglex3())
		print("Scanning motor X3...")
	def stop_scan(self):
		RE.stop()
		print("stopped scanning motor X3") 
	def ui_filename(self):
		return '/cds/home/c/cagee/SND/angle_x3.ui'
class AngleX4Align(PyDMPushButton):
	def __init__(self,parent=None):
		super(AngleX4Align,self).__init__(parent)
		uic.loadUi("/cds/home/c/cagee/SND/angle_x4.ui",self)
		self.startButton.clicked.connect(self.start_scan)
		self.stopButton.clicked.connect(self.stop_scan)
	def anglex4(self):
                # Example: Read values from UI and perform a Bluesky scan
		start_angle = float(self.startLineEdit.text())
		end_angle = float(self.stopLineEdit.text())
		steps = float(self.stepLineEdit.text())
		yield from scan([d14],t4th1,start_angle,end_angle,steps)
	def start_scan(self):
		RE(self.anglex4())
		print("scanning motor X4...")
	def stop_scan(self):
		RE.stop()
		print("Stopped scanning motor X4")
	def ui_filename(self):
		return '/cds/home/c/cagee/SND/angle_x4.ui'
class AngleCC1Align(PyDMPushButton):
	def __init__(self,parent=None):
		super(AngleCC1Align,self).__init__(parent)
		uic.loadUi('/cds/home/c/cagee/SND/angle_cc1.ui',self)
		self.startButton.clicked.connect(self.start_scan)
		self.stopButton.clicked.connect(self.stop_scan)
	def anglecc1(self):
                # Example: Read values from UI and perform a Bluesky scan
		start_angle = float(self.startLineEdit.text())
		end_angle = float(self.stopLineEdit.text())
		steps = float(self.stepLineEdit.text())

		yield from scan([d8],t2th,start_angle,end_angle,steps)
	def start_scan(self):
		RE(self.anglecc1())
		print("scanning motor cc1...")
	def stop_scan(self):
		RE.stop()
		print("Stopped scanning motor cc1")
	def ui_filename(self):
		return '/cds/home/c/cagee/SND/angle_cc1.ui'
class AngleCC2Align(PyDMPushButton):
	def __init__(self,parent=None):
		super(AngleCC2Align,self).__init__(parent)
		uic.loadUi('/cds/home/c/cagee/SND/angle_cc2.ui',self)
		self.startButton.clicked.connect(self.start_scan)
		self.stopButton.clicked.connect(self.stop_scan)
	def anglecc2(self):
                # Example: Read values from UI and perform a Bluesky scan
		start_angle = float(self.startLineEdit.text())
		end_angle = float(self.stopLineEdit.text())
		steps = float(self.stepLineEdit.text())

		yield from scan([d9],t3th,start_angle,end_angle,steps)		
		
	def start_scan(self):
		RE(self.anglecc2())
		print("Scanning motor cc2...")
	def stop_scan(self):
		RE.stop()
		print("Stopped Scanning motor cc2")
	def ui_filename(self):
		return '/cds/home/c/cagee/SND/angle_cc2.ui'

print("Done Scanning")

if __name__=='__main__':
	from pydm import PyDMApplication
	app=QtWidgets.QApplication(sys.argv)
	form=AngleX1Align()
	form.show()
	sys.exit(app.exec_())
