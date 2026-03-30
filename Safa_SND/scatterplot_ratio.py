import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5 import QtWebEngineWidgets, QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QWidget
from pydm.widgets import PyDMRelatedDisplayButton, PyDMPushButton, PyDMScatterPlot
import pydm
from pydm import PyDMApplication
from pydm.widgets.channel import PyDMChannel


#calculate the ratio of two PV/Channels, and then use that for the y axis of PyDM scatterplots in main gui screen
#Specify a new local PV variable to be applied in the qt designer later
class ChannelClass(PyDMChannel):
        def __init__(self,parent=None):
		self.setup_ui()
		#RATIO PV DEFINE:
                # for motor t1th1 x1, scan against ch11/ch10	
		self.ratio_channel=PyDMChannel(address="loc://ch11_ch10?type=float&init=0")
		self.pv11_channel=PyDMChannel(address="ca://XCS:SND:DIO:AMPL_11")
		self.pv10_channel=PyDMChannel(address="ca://XCS:SND:DIO:AMPL_10")

                #connect PV to update method
		self.pv11_channel.value_signal.connect(self.update_ratio)
		self.pv10_channel.value_signal.connect(self.update_ratio)

#	def setup_ui(self):
#		self.ui=uic.loadUi(self,'motors_screen.ui')

# function to create a ratio expression
	def update_ratio(self,*args):
		pv11_value=self.pv11_channel.value
		pv10_value=self.pv10_channel.value
		if pv10_value !=0:
			ratio = pv11_value/pv10_value
                        print("ratio is now", ratio)
                else:
			ratio=0
                        print("ratio is zero")
		self.ratio_channel.put_value(ratio)
                


if __name__=="__main__":
	app=QApplication(sys.argv)
	window=ChannelClass()
	window.show()
	sys.exit(app.exec_())

# Creates a local PV, then create a PyDMChannel object that writes to it

#loc://ch11_ch10?type=float&init=0
		
