##source /cds/group/pcds/pyps/conda/dev_conda before running script
#scan_theta.py referenced for snd_gui.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np
from bluesky import RunEngine
from bluesky import plan_stubs as bps
from bluesky.callbacks.best_effort import BestEffortCallback
from databroker import Broker
from ophyd.signal import EpicsSignal
from ophyd.signal import EpicsSignalRO
from PyQt5 import QtWidgets, uic
from pydm.widgets import PyDMPushButton
from scipy.optimize import curve_fit

UI_DIR = Path(__file__).resolve().parent


def gaussian(x, center, sigma, amplitude, yoffset):
    return amplitude * np.exp(-((x - center) ** 2) / (2 * sigma ** 2)) + yoffset


def scan_fit_center(
    RE,
    motor,
    detector,
    *,
    start,
    stop,
    steps,
    shots_per_step=1,
    move=True,
):
    positions = np.repeat(np.linspace(start, stop, steps), shots_per_step)
    data_x = []
    data_y = []

    def collect(name, doc):
        if name == "event":
            data_x.append(doc["data"][motor.name])
            data_y.append(doc["data"][detector.name])

    token = RE.subscribe(collect)
    RE(bps.rel_list_scan([detector], motor, positions))
    RE.unsubscribe(token)

    xy = {}
    for x, y in zip(data_x, data_y):
        xy.setdefault(x, []).append(y)

    x_unique = np.array(sorted(xy.keys()))
    y_avg = np.array([np.mean(xy[x]) for x in x_unique])

    initial_guess = [
        np.mean(x_unique),
        np.std(x_unique),
        np.max(y_avg),
        np.min(y_avg),
    ]
    popt, _ = curve_fit(gaussian, x_unique, y_avg, p0=initial_guess)
    center, sigma, amplitude, yoffset = popt

    if move:
        RE(bps.mv(motor, float(center)))

    return {
        "x": x_unique,
        "y": y_avg,
        "center": center,
        "sigma": sigma,
        "amplitude": amplitude,
        "yoffset": yoffset,
    }

d12 = EpicsSignalRO("XCS:SND:DIO:AMPL_12", name="diode 12")
d8 = EpicsSignalRO("XCS:SND:DIO:AMPL_8", name="diode 8")
d9 = EpicsSignalRO("XCS:SND:DIO:AMPL_9", name="diode 9")
d11 = EpicsSignalRO("XCS:SND:DIO:AMPL_11", name="diode 11")
d10 = EpicsSignalRO("XCS:SND:DIO:AMPL_10", name="diode 10")
d15 = EpicsSignalRO("XCS:SND:DIO:AMPL_15", name="diode 15")
d14 = EpicsSignalRO("XCS:SND:DIO:AMPL_14", name="diode 14")
d13 = EpicsSignalRO("XCS:SND:DIO:AMPL_13", name="diode 13")

t1th1 = EpicsSignal("XCS:SND:T1:TH1", name="x1 motor")
t1th2 = EpicsSignal("XCS:SND:T1:TH2", name="x2 motor")
t2th = EpicsSignal("XCS:SND:T2:TH", name="cc1 motor")
t3th = EpicsSignal("XCS:SND:T3:TH", name="cc2 motor")
t4th1 = EpicsSignal("XCS:SND:T4:TH1", name="x4 motor")
t4th2 = EpicsSignal("XCS:SND:T4:TH2", name="x3 motor")

HARDWARE_BACKEND = SimpleNamespace(
    t1_th1=t1th1,
    t1_dh_sum=d11,
    t1_th2=t1th2,
    dd_sum=d12,
    t4_th2=t4th2,
    t4_dh_sum=d15,
    t4_th1=t4th1,
    do_sum=d14,
    t2_th=t2th,
    dcc_sum=d8,
    t3_th=t3th,
    dci_sum=d9,
)


def build_simulator_backend(snd_ophyd):
    """
    Expose simulator devices under the same crystal-level names used here.

    The current simulator adapter supports the four delay-branch rocking scans.
    The CC diagnostics are left as ``None`` until equivalent simulator signals
    are exposed.
    """
    return SimpleNamespace(
        t1_th1=snd_ophyd.t1_th1,
        t1_dh_sum=snd_ophyd.t1_dh_sum,
        t1_th2=snd_ophyd.t1_th2,
        dd_sum=snd_ophyd.dd_sum,
        t4_th2=snd_ophyd.t4_th2,
        t4_dh_sum=snd_ophyd.t4_dh_sum,
        t4_th1=snd_ophyd.t4_th1,
        do_sum=snd_ophyd.do_sum,
        t2_th=getattr(snd_ophyd, "t2_th", None),
        dcc_sum=getattr(snd_ophyd, "dcc_sum", None),
        t3_th=getattr(snd_ophyd, "t3_th", None),
        dci_sum=getattr(snd_ophyd, "dci_sum", None),
    )


@dataclass(frozen=True)
class AlignmentSpec:
    ui_path: str
    motor_attr: str
    detector_attr: str
    scan_name: str
    motor_label: str
    detector_label: str
    title_prefix: str


class CrystalAlignBase(PyDMPushButton):
    SPEC: AlignmentSpec | None = None

    def __init__(self, parent=None, backend=None):
        super().__init__(parent)
        if self.SPEC is None:
            raise TypeError("CrystalAlignBase requires a SPEC")

        self.backend = backend if backend is not None else HARDWARE_BACKEND
        self.center = None

        uic.loadUi(self.SPEC.ui_path, self)
        self.startButton.clicked.connect(self.start_scan)
        self.stopButton.clicked.connect(self.stop_scan)
        self.moveToCenter.clicked.connect(self.move_to_center)

        self.RE = RunEngine()
        self.db = Broker.named("temp")
        self.bec = BestEffortCallback()
        self.RE.subscribe(self.bec)

    def _get_device(self, attr):
        device = getattr(self.backend, attr, None)
        if device is None:
            raise RuntimeError(
                f"Backend does not provide '{attr}' needed for {self.SPEC.title_prefix} alignment."
            )
        return device

    @property
    def motor(self):
        return self._get_device(self.SPEC.motor_attr)

    @property
    def detector(self):
        return self._get_device(self.SPEC.detector_attr)

    def _scan_parameters(self):
        if self.startLineEdit.text().strip() == "":
            return None

        return {
            "start": float(self.startLineEdit.text()),
            "stop": float(self.stopLineEdit.text()),
            "steps": int(self.stepLineEdit.text()),
            "shots_per_step": int(self.nShotsLineEdit.text()),
        }
    
    def start_scan(self):
        print(f"Scanning motor {self.SPEC.scan_name}")
        parameters = self._scan_parameters()
        if parameters is None:
            return None

        result = scan_fit_center(
            self.RE,
            self.motor,
            self.detector,
            move=False,
            **parameters,
        )

        center = result["center"]
        sigma = result["sigma"]
        amplitude = result["amplitude"]
        yoffset = result["yoffset"]

        print("Unique X values:", result["x"])
        print("Average Y values:", result["y"])
        print("Fitting rocking curve")
        print("center", center)
        print("sigma", sigma)
        print("amplitude", amplitude)
        print("yoffset", yoffset)

        plt.figure()
        plt.plot(result["x"], result["y"], ".")
        plt.xlabel(self.SPEC.motor_label)
        plt.ylabel(self.SPEC.detector_label)
        plt.plot(
            result["x"],
            gaussian(result["x"], center, sigma, amplitude, yoffset),
            linestyle="--",
            color="r",
        )
        plt.title(
            f"{self.SPEC.title_prefix} Center : {center:.5f} "
            f"FWHM: {2.333 * sigma:.5f}"
        )
        plt.legend()
        plt.show()

        self.center = float(center)
        print("move_to_center", self.center)
        return self.center
 
    def move_to_center(self):
        if self.center is None:
            print("No fitted center available. Run a scan first.")
            return

        print("Moving to", self.center)
        self.RE(bps.mv(self.motor, float(self.center)))
        print(f"Angle {self.SPEC.scan_name} moved to center position ", self.center)

    def stop_scan(self):
        self.RE.stop()
        print(f"Stopped scanning motor {self.SPEC.scan_name}")

    def ui_filename(self):
        return self.SPEC.ui_path


class AngleX1Align(CrystalAlignBase):
    SPEC = AlignmentSpec(
        ui_path=str(UI_DIR / "angle_x1.ui"),
        motor_attr="t1_th1",
        detector_attr="t1_dh_sum",
        scan_name="x1",
        motor_label="t1.th1",
        detector_label="diode 11",
        title_prefix="X1",
    )


class AngleX2Align(CrystalAlignBase):
    SPEC = AlignmentSpec(
        ui_path=str(UI_DIR / "angle_x2.ui"),
        motor_attr="t1_th2",
        detector_attr="dd_sum",
        scan_name="x2",
        motor_label="t1.th2",
        detector_label="diode 12",
        title_prefix="X2",
    )


class AngleX3Align(CrystalAlignBase):
    SPEC = AlignmentSpec(
        ui_path=str(UI_DIR / "angle_x3.ui"),
        motor_attr="t4_th2",
        detector_attr="t4_dh_sum",
        scan_name="x3",
        motor_label="t4.th2",
        detector_label="diode 15",
        title_prefix="X3",
    )


class AngleX4Align(CrystalAlignBase):
    SPEC = AlignmentSpec(
        ui_path=str(UI_DIR / "angle_x4.ui"),
        motor_attr="t4_th1",
        detector_attr="do_sum",
        scan_name="x4",
        motor_label="t4.th1",
        detector_label="diode 14",
        title_prefix="X4",
    )


class AngleCC1Align(CrystalAlignBase):
    SPEC = AlignmentSpec(
        ui_path=str(UI_DIR / "angle_cc1.ui"),
        motor_attr="t2_th",
        detector_attr="dcc_sum",
        scan_name="cc1",
        motor_label="t2.th",
        detector_label="diode 8",
        title_prefix="CC1",
    )


class AngleCC2Align(CrystalAlignBase):
    SPEC = AlignmentSpec(
        ui_path=str(UI_DIR / "angle_cc2.ui"),
        motor_attr="t3_th",
        detector_attr="dci_sum",
        scan_name="cc2",
        motor_label="t3.th",
        detector_label="diode 9",
        title_prefix="CC2",
    )


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    form = AngleX1Align()
    form.show()
    sys.exit(app.exec_())
