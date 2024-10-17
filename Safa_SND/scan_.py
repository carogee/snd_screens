#scan_.py: making small angle motor controls 
import sys
from os import path
from pydm import Display
from PyQt5 import QtWidgets, uic
from bluesky import RunEngine
RE = RunEngine({})
from bluesky.plans import scan
from ophyd.sim import motor, det
from pydm import PyDMApplication
from scan_theta import anglex1, anglex2, anglex3, anglex4, anglecc1, anglecc2
from scan_theta import AngleX1Align, AngleX2Align, AngleX3Align, AngleX4Align, AngleCC1Align, AngleCC2Align
from pydm.widgets.pushbutton import PyDMPushButton
from pydm.widgets import PyDMRelatedDisplayButton
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5 import QtWebEngineWidgets
from PyQt5.QtWidgets import QMainWindow, QWidget
from bluesky.callbacks.best_effort import BestEffortCallback
bec = BestEffortCallback()
RE.subscribe(bec)
from bluesky.utils import install_kicker

#RE(scan([det],motor,1,4,11))

class Angle1(PyDMRelatedDisplayButton):

	def __init__(self, parent=None):
		super(Angle1, self).__init__(parent)
		uic.loadUi('angle_x1.ui', self)
		self.RE=RunEngine()
		self.scanPushButton.clicked.connect(self.start_scan)
#the separate angle control window for X1
	def start_scan(self):
                # Example: Read values from UI and perform a Bluesky scan
		start_angle = float(self.startLineEdit.text())
		end_angle = float(self.stopLineEdit.text())
		steps = float(self.stepLineEdit.text())
		
		scanx1=anglex1(start_angle,end_angle,steps)
		self.RE(scanx1)
		RE(scan([det],motor,start_angle,end_angle,steps))
		print("scanning motor X1...")
	def ui_filename(self):
		return 'angle_x1.ui'

	def ui_filepath(self):
		return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())
#class AngleControls(QMainWindow):
#       def __init__(self,parent=None):
#               super(AngleControls,self).__init__(parent)
#               #load ui file
#               uic.loadUi("angle_controlx1.ui",self)
#               self.angle_input=self.findChild(PyDMLineEdit,"Start")
#               self.angle_input.returnPressed.connect(self.update_angle)
#               self.RE=RunEngine({})
#       def update_angle(self):
                #obtain angle from line-edit
#               angle_value=float(self.angle_input.text())
                #bluesky function call: 
if __name__=='__main__':
	from pydm import PyDMApplication
	app = QtWidgets.QApplication(sys.argv)
	form = Angle1()
	form.show()
	sys.exit(app.exec_())

