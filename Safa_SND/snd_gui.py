import sys
from os import path
from pydm import Display
from PyQt5 import QtWidgets, uic
from bluesky import RunEngine
RE = RunEngine({})
from bluesky.plans import scan
from ophyd.sim import motor, det
from pydm import PyDMApplication

from pydm.widgets.channel import PyDMChannel
#from scan_theta import anglex1, anglex2, anglex3, anglex4, anglecc1, anglecc2 
from pydm.data_plugins.local_plugin import LocalPlugin
from scan_theta import AngleX1Align, AngleX2Align, AngleX3Align, AngleX4Align, AngleCC1Align, AngleCC2Align
from pydm.widgets.pushbutton import PyDMPushButton
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5 import QtWebEngineWidgets, QtCore
from pydm.widgets.channel import PyDMChannel
from pydm.widgets.scatterplot import PyDMScatterPlot
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QWidget
from PyQt5.QtWidgets import QMainWindow, QWidget
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.plan_stubs import stop
bec = BestEffortCallback()
RE.subscribe(bec)

from bluesky.utils import install_kicker
#install_kicker()

class MotorControls(QtWidgets.QWidget):
	
	def __init__(self, parent=None):
		super(MotorControls, self).__init__(parent)

		uic.loadUi('motors_screen.ui', self)
	#attempt to apply ratio to y axis of scatterplot
	
	#	self.scatterplot=self.ui.findChild(PyDMScatterplot, "X1Plot")

#		self.y1=None
#		self.y2=None
	
#		channel1=PyDMChannel(address='ca://XCS:SND:DIO:AMPL_11',value_slot= self.ratio_1(value,'y1'))
#		channel2=PyDMChannel(address='ca://XCS:SND:DIO:AMPL_10',value_slot= self.ratio_2(value,'y2'))

#		channel1.connect()
#		channel2.connect()

#	def ratio_1(self, value, pv):
#		self.y1=value
#		self.update_ratio()
#	def ratio_2(self,value,pv):
#		self.y2=value
#		self.update_ratio()

#PydmRelatedDisplay buttons connect to custom functions:
		self.X1.clicked.connect(self.scan_openx1)
		self.X2.clicked.connect(self.scan_openx2)
		self.X3.clicked.connect(self.scan_openx3)
		self.X4.clicked.connect(self.scan_openx4)
		self.CC1.clicked.connect(self.scan_opencc1)
		self.CC2.clicked.connect(self.scan_opencc2)
	
# the functions that connect to the custom classes from  scan_theta.py
# setwindow flags lines  enable modal pop up window for each motor
#
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
		return 'motors_screen.ui'

	def ui_filepath(self):
		return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())




if __name__=='__main__':
	from pydm import PyDMApplication
	app = QtWidgets.QApplication(sys.argv)
	form = MotorControls()
	form.show()
	sys.exit(app.exec_())
