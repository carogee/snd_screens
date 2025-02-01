##source /cds/group/pcds/pyps/conda/dev_conda before running script
#scan_theta.py referenced for snd_gui.py
from subprocess import check_output

import logging
import json
import sys
import time
import os
import numpy as np

from ophyd.signal import EpicsSignalRO
from ophyd.signal import EpicsSignal
from bluesky import RunEngine
from bluesky.plans import scan, list_scan, count
from bluesky.plan_stubs import abs_set, trigger_and_read, stop
from databroker import Broker, catalog
from ophyd import Component as Cpt
from ophyd import Device

#import relevant pydm/qt 
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5 import QtWebEngineWidgets, QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QWidget

from pydm.widgets import PyDMRelatedDisplayButton, PyDMPushButton
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.utils import install_kicker

from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

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

#RE=RunEngine()
#db = Broker.named('temp')
#bec=BestEffortCallback()
#RE.subscribe(bec)
 
#        Classes for each angle control ui screen with start, end, number of steps inputs
#functions to call in the classes inside each class
# each class for the 6 different buttons/motors
# classes for pop up Buttons in snd_gui.py to call on: 

# Gaussian function for fitting                                                                 
def gaussian(x, center, sigma, amplitude,yoffset):
    return amplitude * np.exp(-((x - center) ** 2) / (2 * sigma ** 2))+yoffset

# Poly1 function for fitting                                                                    
def poly1(x,slop,xoffset,yoffset):
    return slop*(x+xoffset)+yoffset

class CustomBestEffortCallback(BestEffortCallback):
    def __init__(self, data_x, data_y, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_x = data_x
        self.data_y = data_y
    
    def __call__(self, name, doc, escape=False):
        super().__call__(name, doc, escape=escape)  # Call the original BEC method
        # Capture the specific data you want to save
        if 'data' in doc:
            x1_all = doc['data'].get('x1 motor')
            y1_all = doc['data'].get('diode 11')  
            if x1_all is not None:
                self.data_x.append(x1_all)
                self.data_y.append(y1_all)


class AngleX1Align(PyDMPushButton):
    def __init__(self, parent=None):
        super(AngleX1Align, self).__init__(parent)
        uic.loadUi("/cds/home/c/cagee/SND/angle_x1.ui", self)

        self.startButton.clicked.connect(self.start_scan)
        self.stopButton.clicked.connect(self.stop_scan)

        # Initialize RunEngine and Broker
        self.RE = RunEngine()
        self.db = Broker.named('temp')

        # A list to collect scan results
        self.results_x = []
        self.results_y = []

        # Use the custom callback to capture data
        self.bec = CustomBestEffortCallback(self.results_x, self.results_y)
        self.RE.subscribe(self.bec)


    def anglex1(self):
        if not (self.startLineEdit.text().strip()) == "":
            start_angle = float(self.startLineEdit.text())
            end_angle = float(self.stopLineEdit.text())
            steps = int(self.stepLineEdit.text())
            n = 50
            positions1 = np.repeat(np.linspace(start_angle, end_angle, steps), n)
            yield from list_scan([d11], t1th1, positions1)

    def start_scan(self):
        # Read values from UI and perform a Bluesky scan
        print("Scanning motor x1")
        scan_results = self.RE(self.anglex1())
        
        xy_dict = {} #dictionary for unique x and average y values

        # The results collected during the scan are stored in self.results
        x_values = self.results_x
        y_values = self.results_y
        #print("Collected data values x:", x_values)
        #print("Collected data values y:", y_values)

        # Step 2: Populate the dictionary
        for x, y in zip(x_values, y_values):
            if x not in xy_dict:
                xy_dict[x] = []
            xy_dict[x].append(y)

        # Step 3: Compute the averages
        x_unique = []
        y_avg = []

        for x in sorted(xy_dict.keys()):  # Sort keys to maintain order
            x_unique.append(x)
            y_avg.append(np.mean(xy_dict[x]))

        # Print or store the averaged results as needed
        print("Unique X values:", x_unique)
        print("Average Y values:", y_avg)

        print("Fitting rocking curve")
        initial_guess = [np.mean(x_unique), np.std(x_unique), np.max(y_avg),np.min(y_avg)]
        popt, _ = curve_fit(gaussian, x_unique, y_avg, p0=initial_guess)
        center, sigma, amplitude,yoffset = popt
        print("center",popt[0])
        print("sigma",popt[1])
        print("amplitude",popt[2])
        print("yoffset",popt[3])
        
        
        
        fig,axs = plt.subplots(2,2)
        axs[0,0].plot(x_unique,y_avg,'.')
        axs[0,0].set_xlabel('t1.th1')
        #ax.grid()
        
        axs[0,0].plot(x_unique, gaussian(x_unique, *popt), linestyle='--', color='r')
        axs[0,0].set_title('Center : {:.5f}'.format(center)+' FWHM: {:.5f}'.format(2.333*sigma))
        #axs[0,0].legend()
        plt.tight_layout()
        plt.show()

    def stop_scan(self):
        # Implement stop scan logic, if necessary
        print("Stopping scan")
        
    """
    def rocking_fit(self):
        print('Fitting x1 rocking curve')
                                                                                                                   
        x=th1;y=th1_data;                                                                                     
        initial_guess = [np.mean(x), np.std(x), np.max(y),np.min(y)]                                         
        popt, _ = curve_fit(gaussian, x, y, p0=initial_guess)  
        center, sigma, amplitude,yoffset = popt                                                                       
                                                                                                                      
        plt.subplot(2,2,1);                                                                                           
        plt.plot(x,y,'.');plt.xlabel('t1.th1');plt.grid()                                                             
        plt.plot(x, gaussian(x, *popt), linestyle='--', color='r');plt.tight_layout()                                 
        plt.title('Center : {:.5f}'.format(center)+' FWHM: {:.5f}'.format(2.333*sigma))                               
        plt.draw()                                                                                                    
    """
    
    def ui_filename(self):
        return '/cds/home/c/cagee/SND/angle_x1.ui'

class AngleX2Align(PyDMPushButton):
    def __init__(self,parent=None):
        super(AngleX2Align,self).__init__(parent)
        uic.loadUi("/cds/home/c/cagee/SND/angle_x2.ui",self)	
        self.startButton.clicked.connect(self.start_scan)
        self.stopButton.clicked.connect(self.stop_scan)	
    def anglex2(self):
        if not (self.startLineEdit.text().strip()) == "":
            start_angle=float(self.startLineEdit.text())
            end_angle=float(self.stopLineEdit.text())
            steps=int(self.stepLineEdit.text())
            n = 50
            positions = np.repeat(np.linspace(start_angle,end_angle,steps),n)
            yield from list_scan([d12],t1th2,positions)
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
        if not (self.startLineEdit.text().strip()) == "":
            # Example: Read values from UI and perform a Bluesky scan
            start_angle = float(self.startLineEdit.text())
            end_angle = float(self.stopLineEdit.text())
            steps = int(self.stepLineEdit.text())
            n = 50
            positions = np.repeat(np.linspace(start_angle,end_angle,steps),n)
            yield from list_scan([d15],t4th2,positions)
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
        if not (self.startLineEdit.text().strip()) == "":
            start_angle = float(self.startLineEdit.text())
            end_angle = float(self.stopLineEdit.text())
            steps = int(self.stepLineEdit.text())
            n = 50
            positions = np.repeat(np.linspace(start_angle,end_angle,steps),n)
            yield from list_scan([d14],t4th1,positions)
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
        if not (self.startLineEdit.text().strip()) == "":
            start_angle = float(self.startLineEdit.text())
            end_angle = float(self.stopLineEdit.text())
            steps = int(self.stepLineEdit.text())
            n = 50
            positions = np.repeat(np.linspace(start_angle,end_angle,steps),n)
            yield from list_scan([d8],t2th,positions)
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
        if not (self.startLineEdit.text().strip()) == "":
            start_angle = float(self.startLineEdit.text())
            end_angle = float(self.stopLineEdit.text())
            steps = int(self.stepLineEdit.text())
            n = 50
            positions = np.repeat(np.linspace(start_angle,end_angle,steps),n)
            yield from list_scan([d9],t3th,positions)		
		
    def start_scan(self):
        RE(self.anglecc2())
        print("Scanning motor cc2...")
    def stop_scan(self):
        RE.stop()
        print("Stopped Scanning motor cc2")
    def ui_filename(self):
        return '/cds/home/c/cagee/SND/angle_cc2.ui'
"""
if __name__=='__main__':
        from pydm import PyDMApplication
        app=QtWidgets.QApplication(sys.argv)
	form=AngleX1Align()
	form.show()
        form.close()
        sys.exit(app.exec_())
"""
