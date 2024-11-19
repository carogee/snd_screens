from os import path

from qtpy.QtCore import Slot
from qtpy.QtGui import QIntValidator

from pydm import Display


class EventBuilderTimeplot(Display):
    def __init__(self, parent=None, args=None, macros=None):
        """
        Screen to plot time plots based of the ebuild waveform PV.
        Allows adjustement of the timespan via a QLineEdit.
        """
        super().__init__(parent=parent, args=args, macros=macros)

        self.le_timespan.setValidator(QIntValidator())  # only accept int

        # Connect signals
        self.le_timespan.returnPressed.connect(self.update_timespan)
        return

    def ui_filename(self):
        return 'event_builder_timeplot.ui'

    def ui_filepath(self):
        return path.join(path.dirname(path.realpath(__file__)),
                         self.ui_filename())

    @Slot()
    def update_timespan(self):
        timespan = int(self.le_timespan.text())
        print(f'Timespan update to {timespan}s.')
        self.timeplot.setBufferSize(120*timespan)  # assume 120Hz data rate
        self.timeplot.setTimeSpan(timespan)
        return
