import numpy as np
from PyQt6 import QtWidgets

from frontend.AnalysisModePage import AnalysisDialog


class DummyMotorPkg:
    def __init__(self):
        # simple ramp data for rpm and angle, constant zeros for others
        self.time_rpm = np.linspace(0, 1, 128)
        self.motor_rpm = np.linspace(0, 100, 128)
        self.time_angle = self.time_rpm
        self.motor_angleDeg = np.linspace(0, 360, 128)
        self.time_tilt = self.time_rpm
        self.motor_tiltDeg = np.zeros(128)
        self.time_encoder = self.time_rpm
        self.encoder_rpm = np.zeros(128)
        self.encoder_angle = np.zeros(128)
        self.encoder_tilt = np.zeros(128)


def test_perform_bandpass_plots(qtbot, monkeypatch):
    # we can just hand a dummy instance directly; heuristics in
    # performBandpass no longer require a real PackageMotorData object

    dialog = AnalysisDialog()
    qtbot.addWidget(dialog)
    pkg = DummyMotorPkg()
    # perform bandpass - should populate dialog.series with one or more keys
    dialog.performBandpass(pkg)
    assert isinstance(dialog.series, dict)
    assert len(dialog.series) > 0
    # ensure plotted y-values differ from original (some filtering happened)
    for s in dialog.series.values():
        assert 'y' in s and isinstance(s['y'], np.ndarray)
        assert not np.allclose(s['y'], np.linspace(0, 100, len(s['y'])))
