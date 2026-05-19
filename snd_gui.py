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
#from pydm import PyDMApplication

from pydm.widgets.channel import PyDMChannel
#from scan_theta import anglex1, anglex2, anglex3, anglex4, anglecc1, anglecc2 
from pydm.data_plugins.local_plugin import LocalPlugin
from scan_theta import AngleX1Align, AngleX2Align, AngleX3Align, AngleX4Align, AngleCC1Align, AngleCC2Align
from dd_in import DDCrystal_MoveIn
from pydm.widgets.pushbutton import PyDMPushButton
from pydm.widgets import PyDMLabel
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

from qtpy.QtWidgets import QTableWidgetItem, QHeaderView, QLabel
from qtpy.QtCore import Qt
from pydm.widgets.display_format import DisplayFormat
from qtpy.QtGui import QColor

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
        #uic.loadUi('/cds/home/c/cagee/SND/motors_screen.ui', self)
        #uic.loadUi(file_path, self)

        #PydmRelatedDisplay buttons connect to custom functions:                                           
        self.X1.clicked.connect(self.scan_openx1)
        self.X2.clicked.connect(self.scan_openx2)
        self.X3.clicked.connect(self.scan_openx3)
        self.X4.clicked.connect(self.scan_openx4)
        self.CC1.clicked.connect(self.scan_opencc1)
        self.CC2.clicked.connect(self.scan_opencc2)
        self.DDCrystalIn.clicked.connect(self.move_ddcrystalin)

        # Create a QLabel to display the average value
        #self.average_label = QtWidgets.QLabel(self)  # Use QLabel from QtWidgets
        #self.average_label.setGeometry(223, 100, 200, 50)  # Set position and size
        #self.average_label.setText("Average: 0.0")

        # Set up a timer to update the average value every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_average)
        self.timer.start(1000)  # Update every second
        print("initialized timer")

        self.setup_pv_table()

    #def update_average(self):
    #    # Get the averaged value and update the label
    #    averaged_value_dcc = self.my_device.dcc_signal.get()
    #    averaged_value_ch12 = self.my_device.ch12.get()
    #    averaged_ratio = averaged_value_ch12/averaged_value_dcc
    #    self.average_label.setText(f"{averaged_ratio:.2f}")
    def update_average(self):
        """
        Calculates the ratio and updates the 'Intensity Ratio' cell in the table.
        """
        try:
            averaged_value_dcc = self.my_device.dcc_signal.get()
            averaged_value_ch12 = self.my_device.ch12.get()

            # Prevent a crash if the denominator is zero
            if averaged_value_dcc == 0:
                ratio_text = "N/A (Div 0)"
            else:
                # This is your calculation
                averaged_ratio = averaged_value_ch12 / averaged_value_dcc
                ratio_text = f"{averaged_ratio:.4f}" # Format to 4 decimal places

            # Update the specific label inside our table.
            # The 'hasattr' check prevents an error if the label doesn't exist yet.
            if hasattr(self, 'intensity_ratio_label'):
                self.intensity_ratio_label.setText(ratio_text)

        except Exception as e:
            # This will catch any other unexpected errors during the calculation
            # and prevent your whole GUI from crashing.
            print(f"Error during average update: {e}")
            if hasattr(self, 'intensity_ratio_label'):
                self.intensity_ratio_label.setText("Error")


    def setup_pv_table(self):
        """
        Populates the table with a mix of PV-driven and code-driven values.
        """

        table_data = [
            {"description": "CC Energy (eV)",       "pv": "XCS:SND:CALC:E2"},
            {"description": "Time Delay (ps)",      "pv": "XCS:SND:CALC:Delay"},
            {"description": "Intensity Ratio (1s)"}, 
            {"description": "Delay Energy (eV)",    "pv": "XCS:SND:CALC:E1"},
        ]

        table = self.ui.PVTable
        table.setRowCount(len(table_data))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Parameter", "Value"])
        
        light_grey_color = QColor("#F0F0F0") # A pleasant light grey
        white_background_style = "background-color: white;"

        # --- CHANGE #2: The loop logic ---
        # This loop now checks if a row is for a PV or for our special case.
        for row_index, item in enumerate(table_data):
            description_text = item["description"]
            description_widget_item = QTableWidgetItem(description_text)
            description_widget_item.setBackground(light_grey_color)
            table.setItem(row_index, 0, description_widget_item)

            # Check if the row has a PV defined
            if "pv" in item:
                # This is a normal PV row, so we use a PyDMLabel
                value_label = PyDMLabel()
                value_label.channel = f"ca://{item['pv']}"
                value_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                value_label.setStyleSheet(white_background_style)
                if item["description"] == "Delay Energy (eV)":
                    value_label.precisionFromPV = False
                    # Set the display format to Scientific.
                    value_label.displayFormat = DisplayFormat.Exponential
                    # For scientific notation, a lower precision is usually desired.
                    value_label.precision = 2
                else:
                    value_label.displayFormat = DisplayFormat.Decimal
                    value_label.precisionFromPV = True
                    value_label.precision = 3
                table.setCellWidget(row_index, 1, value_label)
            else:
                # --- CHANGE #3: Create a regular QLabel and save a reference ---
                # This is our special "Intensity Ratio" row
                # 1. Create a standard QLabel
                value_label = QLabel("Calculating...") # Initial text
                value_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                value_label.setStyleSheet(white_background_style)
                # 2. Save this label as an attribute of the class.
                #    This allows the update_average function to find it later.
                self.intensity_ratio_label = value_label
            
                # 3. Place the label in the table cell
                table.setCellWidget(row_index, 1, self.intensity_ratio_label)


        desired_row_height = 32
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(desired_row_height)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Style the header to match the medium grey in the image
        header_style = """
            QHeaderView::section {
                background-color: #C0C0C0; /* Medium grey background */
                color: black;              /* Black text */
                font-weight: bold;
                padding: 4px;
            }
        """
        table.horizontalHeader().setStyleSheet(header_style)

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


    def move_ddcrystalin(self):
        if not (self.DDCrystal_LineEdit.text().strip()) == "":
            dd_in = float(self.DDCrystal_LineEdit.text())
            command_T1_Y1 = f'caput XCS:SND:T1:Y1 {dd_in}'
            os.system(command_T1_Y1)
            print("T1:Y1 moved to ",dd_in)

        if not (self.DDCrystal_LineEdit_1.text().strip()) == "":
            dd_in = float(self.DDCrystal_LineEdit_1.text())
            command_T4_Y1 = f'caput XCS:SND:T4:Y1 {dd_in}'
            os.system(command_T4_Y1)
            print("T4:Y1 moved to ",dd_in)


    def ui_filename(self):
        return file_path

    def ui_filepath(self):
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())
   
 
if __name__=='__main__':
    from pydm import PyDMApplication
    app = PyDMApplication(use_main_window=False)
    display = MyDisplay()
    display.show()
    sys.exit(app.exec_())
