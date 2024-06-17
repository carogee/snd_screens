from os import path

from qtpy.QtCore import Slot
from qtpy.QtGui import QFont, QIntValidator

from pydm import Display
from ophyd import EpicsSignal


AXIS_LABEL_FONT_SIZE = 5
TICK_FONT = QFont()
TICK_FONT.setPixelSize(16)


class EventBuilder(Display):
    def __init__(self, parent=None, args=None, macros=None):
        """
        Simple screen to make correlation plots between two variables from an
        EventBuilder IOC.
        To start, run:
            pydm event_builder.py <EVENTBUILD_PV>
        """
        super().__init__(parent=parent, args=args, macros=macros)

        # Get curve and buffer
        self.curve = self.event_plot._curves[0]
        self.le_buffer.setValidator(QIntValidator())  # only accept int
        self.le_buffer.setText(str(self.curve._bufferSize))

        # Get EventBuilder PV and its description
        event_builder_pv = self.event_plot.channels()[0].address
        event_builder_pv = event_builder_pv.split('//')[1]
        self.event_builder_pv = event_builder_pv.split('.VALA')[0]
        description_pv = self.event_builder_pv + ':DESC'
        self.description_signal = EpicsSignal(description_pv, string=True)
        self.parse_description()

        self.set_plot_layout()
        self.update_axis_label()

        # Connect signals
        self.cb_x.currentIndexChanged.connect(self.update_plot_axis)
        self.cb_y.currentIndexChanged.connect(self.update_plot_axis)
        self.le_buffer.returnPressed.connect(self.update_buffer_size)
        return

    def ui_filename(self):
        return 'event_builder.ui'

    def ui_filepath(self):
        return path.join(
            path.dirname(path.realpath(__file__)),
            self.ui_filename()
            )

    def parse_description(self):
        """
        Parse the EventBuilder description PV.
        This PV contains a comma-separated description of each entries in the
        EventBuilder PV. It is converted to a list and passed to the combo
        boxes.
        """
        description = self.description_signal.get()
        self.entries = description.split(',')
        self.num_entries = len(self.entries)
        print(f'Event builder entries (total {self.num_entries}): '
              + ', '.join(self.entries) + '.')

        # add EventBuild entries to combo boxes
        self.cb_x.clear()
        self.cb_y.clear()
        self.cb_x.addItems(self.entries)
        self.cb_y.addItems(self.entries)
        return

    @Slot()
    def update_buffer_size(self):
        bufferSize = int(self.le_buffer.text())
        self.curve._bufferSize = bufferSize
        self.curve.initialize_buffer()
        print(f'New buffer size: {self.curve._bufferSize}')
        return

    @Slot()
    def update_plot_axis(self):
        """
        Updates the plot based on the choice made in the x and y combo box.
        """
        self.curve.initialize_buffer()
        self.curve.x_idx = self.cb_x.currentIndex()
        self.curve.y_idx = self.cb_y.currentIndex()

        print(f"x: {self.cb_x.currentText()}\ny: {self.cb_y.currentText()}")

        self.update_axis_label()
        return

    def update_axis_label(self):
        x_label = self.cb_x.currentText()
        y_label = self.cb_y.currentText()
        self.event_plot.setLabel(
            'bottom',
            f'<font size="{AXIS_LABEL_FONT_SIZE}">{x_label}<\font size>'
        )
        self.event_plot.setLabel(
            'Axis 1',
            f'<font size="{AXIS_LABEL_FONT_SIZE}">{y_label}<\font size>'
        )
        return

    def set_plot_layout(self):
        """
        Various formatting of the EventBuilder plot.
        Run once when starting the GUI.
        """
        # grid
        self.event_plot.showGrid(x=True, y=True, alpha=0.8)

        # tick font
        self.event_plot.getAxis('bottom').setTickFont(TICK_FONT)
        self.event_plot.getAxis('Axis 1').setTickFont(TICK_FONT)
        return
