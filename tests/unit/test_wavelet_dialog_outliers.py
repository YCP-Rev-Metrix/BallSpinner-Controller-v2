import numpy as np
from frontend.WaveletDialog import WaveletDialog
from PyQt6 import QtWidgets

class OutlierPkg:
    def __init__(self):
        # one small series and one huge series
        self.time_rpm = np.arange(10)
        self.motor_rpm = np.linspace(0,1,10)
        self.time_angle = np.arange(10)
        # angle series with huge values
        self.motor_angleDeg = np.linspace(0,1e9,10)
        # others empty
        self.time_tilt = np.array([])
        self.motor_tiltDeg = np.array([])
        self.time_encoder = np.array([])
        self.encoder_rpm = np.array([])
        self.encoder_angle = np.array([])
        self.encoder_tilt = np.array([])


def test_auto_uncheck_outlier(qtbot):
    from frontend import WaveletDialog as _WD
    class DummyHelper:
        def __init__(self, parent=None):
            pass
        def exec(self):
            return QtWidgets.QDialog.DialogCode.Accepted
        def get_list(self):
            # specify a positive order, since the dialog now requires it
            return [{'family': 'db', 'family_label': 'Daubechies', 'type': 'db2', 'order': 1}]
    _WD.WavletHelperWidget = DummyHelper
    dlg = WaveletDialog()
    qtbot.addWidget(dlg)
    pkg = OutlierPkg()
    dlg.performWavelet(pkg)
    chk = dlg.seriesChecks['motor_angle']
    assert chk is not None
    assert not chk.isChecked()
    assert dlg.seriesChecks['motor_rpm'].isChecked()

    # rerunning should preserve checkbox state
    dlg.performWavelet(pkg)
    assert not dlg.seriesChecks['motor_angle'].isChecked()
