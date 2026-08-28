##source /cds/group/pcds/pyps/conda/dev_conda before running script
#scan_theta.py referenced for snd_gui.py
from subprocess import check_output

import logging
import json
import sys
import time
import os
import numpy as np
import bluesky.plans
import bluesky.plan_stubs

from ophyd.signal import EpicsSignalRO
from ophyd.signal import EpicsSignal
from bluesky import RunEngine
from bluesky.plans import scan, list_scan, rel_list_scan, count
from bluesky import plan_stubs as bps
from bluesky.plan_stubs import abs_set, trigger_and_read, stop, sleep
from databroker import Broker, catalog
from ophyd import Component as Cpt
from ophyd import Device
from epics import caput
from os import path

#import relevant pydm/qt 
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5 import QtWebEngineWidgets, QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QWidget


from pydm.widgets import PyDMRelatedDisplayButton, PyDMPushButton
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.utils import install_kicker

from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

from pcdsdevices.sim import FastMotor, SlowMotor
sim_x = SlowMotor(name='x')

d12=EpicsSignalRO("XCS:SND:DIO:AMPL_12",name="diode 12") #define PV
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

current_directory = os.getcwd()
print("current directory", current_directory)

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

# Poly function for fitting
def poly(x,slop,xoffset,yoffset):
    return slop*(x+xoffset)+yoffset

# Default scan input values, applied to each Align popup after its UI loads.
def set_scan_defaults(widget):
    widget.startLineEdit.setText('-0.002')   # start range (rel)
    widget.stopLineEdit.setText('0.002')     # stop range (rel)
    widget.stepLineEdit.setText('21')        # number of steps
    widget.nShotsLineEdit.setText('60')      # number of shots

# Render the normalized data + fit either onto an embedded Qt canvas (if given)
# or into a standalone matplotlib window (fallback, original behavior).
# On the embedded canvas the most recent 2 scans and their fits are kept and
# shown together (latest emphasized, previous faded), with a legend.
def render_fit(canvas, x, y_norm, fit_norm, xlabel, ylabel, title):
    if canvas is not None:
        # Persist the last 2 (scan, fit) pairs on the canvas across runs.
        if not hasattr(canvas, 'scan_history'):
            canvas.scan_history = []
        canvas.scan_history.append((np.array(x), np.array(y_norm), np.array(fit_norm)))
        canvas.scan_history = canvas.scan_history[-2:]

        ax = canvas.ax
        ax.clear()
        colors = {'latest': 'C0', 'previous': 'C1'}
        n = len(canvas.scan_history)
        for i, (xh, yh, fh) in enumerate(canvas.scan_history):
            age = 'latest' if i == n - 1 else 'previous'
            c = colors[age]
            alpha = 1.0 if age == 'latest' else 0.45
            ax.plot(xh, yh, marker='.', linestyle='none', color=c, alpha=alpha,
                    label='scan ({})'.format(age))
            ax.plot(xh, fh, linestyle='--', color=c, alpha=alpha,
                    label='fit ({})'.format(age))
        ax.set_xlabel(xlabel, fontsize=8)
        ax.set_ylabel(ylabel, fontsize=8)
        ax.set_title(title, fontsize=8)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=6)
        canvas.fig.tight_layout()
        canvas.draw_idle()
    else:
        plt.figure()
        plt.plot(x, y_norm, marker='.', linestyle='none', label='scan')
        plt.plot(x, fit_norm, linestyle='--', color='r', label='fit')
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        plt.legend()
        plt.show()

class CustomBestEffortCallback(BestEffortCallback):
    def __init__(self, data_x, data_y, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_x = data_x
        self.data_y = data_y
    
    def __call__(self, name, doc, escape=False):
        super().__call__(name, doc, escape=escape)  # Call the original BEC method
        # Capture the specific data you want to save
        # Retrieve all values containing 'motor'

        if 'data' in doc:
            for key in doc['data'].keys():
                if 'motor' in key:
                    x_all = doc['data'].get(key)
                    if x_all != None:
                        self.data_x.append(x_all)
                if 'diode' in key:
                    y_all = doc['data'].get(key)
                    if y_all != None:
                        self.data_y.append(y_all)


class AngleX1Align(PyDMPushButton):
    def __init__(self, parent=None, canvas=None):
        super(AngleX1Align, self).__init__(parent)
        self.canvas = canvas
        file_path = os.path.join(current_directory, 'angle_x1.ui')
        uic.loadUi(file_path, self)
        set_scan_defaults(self)

        self.startButton.clicked.connect(self.start_scan)
        self.stopButton.clicked.connect(self.stop_scan)
        self.moveToCenter.clicked.connect(self.move_to_center)

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
            n = int(self.nShotsLineEdit.text())
            positions = np.repeat(np.linspace(start_angle, end_angle, steps), n)
            yield from rel_list_scan([d11], t1th1, positions)


    def start_scan(self):
        #attempt to do relative position scan with the daq
        print("Scanning motor x1")
        """
        # Add the desired directory to the sys.path
        sys.path.append('/cds/group/pcds/pyps/apps/hutch-python/xcs/xcs')
        # Now you should be able to import xcs.db
        from xcs.db import daq
        if not (self.startLineEdit.text().strip()) == "":
            start_angle = float(self.startLineEdit.text())
            end_angle = float(self.stopLineEdit.text())
            steps = int(self.stepLineEdit.text())
            n = 3
            positions = np.repeat(np.linspace(start_angle, end_angle, steps), n)
            
            daq.begin(record=False,events=None)
            for ii in enumerate(positions):
                print("position",positions[ii])
                sim_x.move(positions[ii])
                #time.sleep(0.05)
            daq.end_run()
            daq.disconnect()
        """
        # Read values from UI and perform a Bluesky scan
        print("Scanning motor x1")
        scan_results = self.RE(self.anglex1())
        
        xy_dict = {} #dictionary for unique x and average y values

        # The results collected during the scan are stored in self.results
        x_values = self.results_x
        y_values = self.results_y

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
        
        # Normalize data and fit so baseline -> 0 and peak -> 1
        x_fit = np.array(x_unique)
        y_norm = (np.array(y_avg) - yoffset) / amplitude
        fit_norm = (gaussian(x_fit, *popt) - yoffset) / amplitude

        render_fit(self.canvas, x_fit, y_norm, fit_norm,
                   't1.th1', 'diode 11 (normalized)',
                   'X1 Center : {:.5f}'.format(center)+' FWHM: {:.5f}'.format(2.333*sigma))

        self.center = popt[0]
        print("move_to_center", self.center)
        return self.center
        #self.move_to_center(center)

    def move_to_center(self):
        print("Moving to", self.center)
        command_move = f'caput XCS:SND:T1:TH1 {self.center}'
        os.system(command_move)
        print("Angle x1 moved to center position ", self.center)


    def stop_scan(self):
        self.RE.stop()
        print("Stopped scanning x1 motor")
    
    def ui_filename(self):
        return file_path

class AngleX2Align(PyDMPushButton):
    def __init__(self, parent=None, canvas=None):
        super(AngleX2Align, self).__init__(parent)
        self.canvas = canvas
        file_path = os.path.join(current_directory, 'angle_x2.ui')
        uic.loadUi(file_path, self)
        set_scan_defaults(self)

        self.startButton.clicked.connect(self.start_scan)
        self.stopButton.clicked.connect(self.stop_scan)
        self.moveToCenter.clicked.connect(self.move_to_center)

        # Initialize RunEngine and Broker                                                             
        self.RE = RunEngine()
        self.db = Broker.named('temp')

        # A list to collect scan results                                                              
        self.results_x = []
        self.results_y = []

        # Use the custom callback to capture data                                                     
        self.bec = CustomBestEffortCallback(self.results_x, self.results_y)
        self.RE.subscribe(self.bec)


    def anglex2(self):
        if not (self.startLineEdit.text().strip()) == "":
            start_angle = float(self.startLineEdit.text())
            end_angle = float(self.stopLineEdit.text())
            steps = int(self.stepLineEdit.text())
            n = int(self.nShotsLineEdit.text())
            positions = np.repeat(np.linspace(start_angle, end_angle, steps), n)
            yield from rel_list_scan([d12], t1th2, positions)
    
    def start_scan(self):
        # Read values from UI and perform a Bluesky scan                                              
        print("Scanning motor x2")
        scan_results = self.RE(self.anglex2())
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

        # Normalize data and fit so baseline -> 0 and peak -> 1
        x_fit = np.array(x_unique)
        y_norm = (np.array(y_avg) - yoffset) / amplitude
        fit_norm = (gaussian(x_fit, *popt) - yoffset) / amplitude

        render_fit(self.canvas, x_fit, y_norm, fit_norm,
                   't1.th2', 'diode 12 (normalized)',
                   'X2 Center : {:.5f}'.format(center)+' FWHM: {:.5f}'.format(2.333*sigma))

        self.center = popt[0]
        print("move_to_center", self.center)
        return self.center
 
    def move_to_center(self):
        print("Moving to", self.center)
        command_move = f'caput XCS:SND:T1:TH2 {self.center}'
        os.system(command_move)
        print("Angle x2 moved to center position ", self.center)

    def stop_scan(self):
        self.RE.stop()
        print("Stopped scanning motor X2")
    def ui_filename(self):
        return file_path
   
class AngleX3Align(PyDMPushButton):
    def __init__(self, parent=None, canvas=None):
        super(AngleX3Align, self).__init__(parent)
        self.canvas = canvas
        file_path = os.path.join(current_directory, 'angle_x3.ui')
        uic.loadUi(file_path, self)
        set_scan_defaults(self)

        self.startButton.clicked.connect(self.start_scan)
        self.stopButton.clicked.connect(self.stop_scan)
        self.moveToCenter.clicked.connect(self.move_to_center)

        # Initialize RunEngine and Broker                                                             
        self.RE = RunEngine()
        self.db = Broker.named('temp')

        # A list to collect scan results                                                              
        self.results_x = []
        self.results_y = []

        # Use the custom callback to capture data                                                     
        self.bec = CustomBestEffortCallback(self.results_x, self.results_y)
        self.RE.subscribe(self.bec)


    def anglex3(self,*args, delay=1, **kwargs):
        if not (self.startLineEdit.text().strip()) == "":
            start_angle = float(self.startLineEdit.text())
            end_angle = float(self.stopLineEdit.text())
            steps = int(self.stepLineEdit.text())
            n = int(self.nShotsLineEdit.text())
            positions = np.repeat(np.linspace(start_angle, end_angle, steps), n)
            yield from rel_list_scan([d15], t4th2, positions)
            #detectors = [d15]
            #def one_nd_step_with_delay(detectors, step, positions):
            #    "This is a copy of bluesky.plan_stubs.one_nd_step with a sleep added."
            #    motors = step.keys()
            #    yield from bluesky.plan_stubs.move_per_step(step, positions)
            #    yield from bluesky.plan_stubs.sleep(delay)
            #    yield from bluesky.plan_stubs.trigger_and_read(list(detectors) + list(t4th2))

            #kwargs.setdefault('per_step', one_nd_step_with_delay)
            #yield from bluesky.plans.rel_list_scan(*args, **kwargs)

    def start_scan(self):
        # Read values from UI and perform a Bluesky scan                                                       
        print("Scanning motor x3")
        scan_results = self.RE(self.anglex3())
        xy_dict = {} #dictionary for unique x and average y values                                           
        # The results collected during the scan are stored in self.results  
        x_values = self.results_x
        y_values = self.results_y

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

        # Normalize data and fit so baseline -> 0 and peak -> 1
        x_fit = np.array(x_unique)
        y_norm = (np.array(y_avg) - yoffset) / amplitude
        fit_norm = (gaussian(x_fit, *popt) - yoffset) / amplitude

        render_fit(self.canvas, x_fit, y_norm, fit_norm,
                   't4.th2', 'diode 15 (normalized)',
                   'X3 Center : {:.5f}'.format(center)+' FWHM: {:.5f}'.format(2.333*sigma))
        
        self.center = popt[0]
        print("move_to_center", self.center)
        return self.center
        #self.move_to_center(center)                                                                                                          

    def move_to_center(self):
        print("Moving to", self.center)
        command_move = f'caput XCS:SND:T4:TH2 {self.center}'
        os.system(command_move)
        print("Angle x3 moved to center position ", self.center)

    def stop_scan(self):
        self.RE.stop()
        print("stopped scanning motor X3") 

    def ui_filename(self):
        return file_path

class AngleX4Align(PyDMPushButton):
    def __init__(self, parent=None, canvas=None):
        super(AngleX4Align, self).__init__(parent)
        self.canvas = canvas
        file_path = os.path.join(current_directory, 'angle_x4.ui')
        uic.loadUi(file_path, self)
        set_scan_defaults(self)

        self.startButton.clicked.connect(self.start_scan)
        self.stopButton.clicked.connect(self.stop_scan)
        self.moveToCenter.clicked.connect(self.move_to_center)

        # Initialize RunEngine and Broker                                                             
        self.RE = RunEngine()
        self.db = Broker.named('temp')

        # A list to collect scan results                                                              
        self.results_x = []
        self.results_y = []

        # Use the custom callback to capture data                                                     
        self.bec = CustomBestEffortCallback(self.results_x, self.results_y)
        self.RE.subscribe(self.bec)


    def anglex4(self):
        if not (self.startLineEdit.text().strip()) == "":
            start_angle = float(self.startLineEdit.text())
            end_angle = float(self.stopLineEdit.text())
            steps = int(self.stepLineEdit.text())
            n = int(self.nShotsLineEdit.text())
            positions = np.repeat(np.linspace(start_angle, end_angle, steps), n)
            yield from rel_list_scan([d14], t4th1, positions)
    
    def start_scan(self):
        # Read values from UI and perform a Bluesky scan                                                       
        print("Scanning motor x1")
        scan_results = self.RE(self.anglex4())
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

        # Normalize data and fit so baseline -> 0 and peak -> 1
        x_fit = np.array(x_unique)
        y_norm = (np.array(y_avg) - yoffset) / amplitude
        fit_norm = (gaussian(x_fit, *popt) - yoffset) / amplitude

        render_fit(self.canvas, x_fit, y_norm, fit_norm,
                   't4.th1', 'diode 14 (normalized)',
                   'X4 Center : {:.5f}'.format(center)+' FWHM: {:.5f}'.format(2.333*sigma))
        
        self.center = popt[0]
        print("move_to_center", self.center)
        return self.center
        #self.move_to_center(center)                                                                                                          

    def move_to_center(self):
        print("Moving to", self.center)
        command_move = f'caput XCS:SND:T4:TH1 {self.center}'
        os.system(command_move)
        print("Angle x4 moved to center position ", self.center)

    def stop_scan(self):
        self.RE.stop()
        print("Stopped scanning motor X4")

    def ui_filename(self):
        return file_path

class AngleCC1Align(PyDMPushButton):
    def __init__(self, parent=None, canvas=None):
        super(AngleCC1Align, self).__init__(parent)
        self.canvas = canvas
        file_path = os.path.join(current_directory, 'angle_cc1.ui')
        uic.loadUi(file_path, self)
        set_scan_defaults(self)

        self.startButton.clicked.connect(self.start_scan)
        self.stopButton.clicked.connect(self.stop_scan)
        self.moveToCenter.clicked.connect(self.move_to_center)

        # Initialize RunEngine and Broker                                                             
        self.RE = RunEngine()
        self.db = Broker.named('temp')

        # A list to collect scan results                                                              
        self.results_x = []
        self.results_y = []

        # Use the custom callback to capture data                                                     
        self.bec = CustomBestEffortCallback(self.results_x, self.results_y)
        self.RE.subscribe(self.bec)


    def anglecc1(self):
        if not (self.startLineEdit.text().strip()) == "":
            start_angle = float(self.startLineEdit.text())
            end_angle = float(self.stopLineEdit.text())
            steps = int(self.stepLineEdit.text())
            n = int(self.nShotsLineEdit.text())
            positions = np.repeat(np.linspace(start_angle, end_angle, steps), n)
            yield from rel_list_scan([d8], t2th, positions)

    def start_scan(self):
        # Read values from UI and perform a Bluesky scan                                                       
        print("Scanning motor cc1")
        scan_results = self.RE(self.anglecc1())

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

        # Normalize data and fit so baseline -> 0 and peak -> 1
        x_fit = np.array(x_unique)
        y_norm = (np.array(y_avg) - yoffset) / amplitude
        fit_norm = (gaussian(x_fit, *popt) - yoffset) / amplitude

        render_fit(self.canvas, x_fit, y_norm, fit_norm,
                   't2.th', 'diode 8 (normalized)',
                   'CC1 Center : {:.5f}'.format(center)+' FWHM: {:.5f}'.format(2.333*sigma))

        self.center = popt[0]
        print("move_to_center", self.center)
        return self.center
        #self.move_to_center(center)                                                                                                          

    def move_to_center(self):
        print("Moving to", self.center)
        command_move = f'caput XCS:SND:T2:TH {self.center}'
        os.system(command_move)
        print("Angle cc1 moved to center position ", self.center)

    def stop_scan(self):
        self.RE.stop()
        print("Stopped scanning motor cc1")

    def ui_filename(self):
        return file_path

class AngleCC2Align(PyDMPushButton):
    def __init__(self, parent=None, canvas=None):
        super(AngleCC2Align, self).__init__(parent)
        self.canvas = canvas
        file_path = os.path.join(current_directory, 'angle_cc2.ui')
        uic.loadUi(file_path, self)
        set_scan_defaults(self)

        self.startButton.clicked.connect(self.start_scan)
        self.stopButton.clicked.connect(self.stop_scan)
        self.moveToCenter.clicked.connect(self.move_to_center)

        # Initialize RunEngine and Broker                                                             
        self.RE = RunEngine()
        self.db = Broker.named('temp')

        # A list to collect scan results                                                              
        self.results_x = []
        self.results_y = []

        # Use the custom callback to capture data                                                     
        self.bec = CustomBestEffortCallback(self.results_x, self.results_y)
        self.RE.subscribe(self.bec)


    def anglecc2(self):
        if not (self.startLineEdit.text().strip()) == "":
            start_angle = float(self.startLineEdit.text())
            end_angle = float(self.stopLineEdit.text())
            steps = int(self.stepLineEdit.text())
            n = int(self.nShotsLineEdit.text())
            positions = np.repeat(np.linspace(start_angle, end_angle, steps), n)
            yield from rel_list_scan([d9], t3th, positions)

    def start_scan(self):
        # Read values from UI and perform a Bluesky scan                                                       
        print("Scanning motor cc2")
        scan_results = self.RE(self.anglecc2())
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

        # Normalize data and fit so baseline -> 0 and peak -> 1
        x_fit = np.array(x_unique)
        y_norm = (np.array(y_avg) - yoffset) / amplitude
        fit_norm = (gaussian(x_fit, *popt) - yoffset) / amplitude

        render_fit(self.canvas, x_fit, y_norm, fit_norm,
                   't3.th', 'diode 9 (normalized)',
                   'CC2 Center : {:.5f}'.format(center)+' FWHM: {:.5f}'.format(2.333*sigma))

        self.center = popt[0]
        print("move_to_center", self.center)
        return self.center
        #self.move_to_center(center)                                                                                                          

    def move_to_center(self):
        print("Moving to", self.center)
        command_move = f'caput XCS:SND:T3:TH {self.center}'
        os.system(command_move)
        print("Angle cc2 moved to center position ", self.center)

    def stop_scan(self):
        self.RE.stop()
        print("Stopped Scanning motor cc2")

    def ui_filename(self):
        return file_path

"""
if __name__=='__main__':
        from pydm import PyDMApplication
        app=QtWidgets.QApplication(sys.argv)
	form=AngleX1Align()
	form.show()
        form.close()
        sys.exit(app.exec_())
"""
