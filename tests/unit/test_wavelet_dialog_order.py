import numpy as np
from frontend.WaveletDialog import WaveletDialog
from frontend.WavletHelperWidget import WavletHelperWidget
from PyQt6 import QtWidgets
import pytest

def test_helper_order_control(qtbot):
    """Helper should expose an order spin box and return its value."""
    helper = WavletHelperWidget()
    qtbot.addWidget(helper)
    helper.add_row()
    # header should include order column
    header_item = helper.tblList.horizontalHeaderItem(2)
    assert header_item is not None and header_item.text() == 'Order'
    # there should now be one row with a spin box in column 2
    sb = helper.tblList.cellWidget(0, 2)
    assert isinstance(sb, QtWidgets.QSpinBox)
    # default minimum should be 1
    assert sb.minimum() == 1
    assert sb.value() == 1
    sb.setValue(3)
    lst = helper.get_list()
    assert len(lst) == 1
    assert lst[0]['order'] == 3


class SamplePkg:
    def __init__(self):
        # create a simple ramp so we can observe a change when order varies
        self.time_rpm = np.linspace(0, 1, 50)
        self.motor_rpm = np.sin(2 * np.pi * self.time_rpm)
        # other attributes (required by the dialog) can be empty
        self.time_angle = np.array([])
        self.motor_angleDeg = np.array([])
        self.time_tilt = np.array([])
        self.motor_tiltDeg = np.array([])
        self.time_encoder = np.array([])
        self.encoder_rpm = np.array([])
        self.encoder_angle = np.array([])
        self.encoder_tilt = np.array([])


def test_wavelet_order_affects_results(qtbot):
    """Different integer orders should produce nonidentical detail arrays."""
    dlg = WaveletDialog()
    qtbot.addWidget(dlg)
    pkg = SamplePkg()

    # first run with order 1
    dlg.performWavelet(pkg, wavelet=('db2', 1))
    assert dlg._wave_results, "wave_results should not be empty"
    # grab the sole detail array
    series_key = next(iter(dlg._wave_results))
    details1 = dlg._wave_results[series_key][1]
    assert len(details1) == 1
    detail1 = next(iter(details1.values()))

    # run again with order=2 (higher order gives different detail)
    dlg.performWavelet(pkg, wavelet=('db2', 2))
    assert dlg._wave_results
    details2 = dlg._wave_results[series_key][1]
    detail2 = next(iter(details2.values()))

    # arrays should be same length but not bit-for-bit identical
    assert detail1.shape == detail2.shape
    # use array_equal to detect even tiny boundary differences
    assert not np.array_equal(detail1, detail2)
    # sanity check that there is at least some difference magnitude
    assert np.max(np.abs(detail1 - detail2)) > 0
