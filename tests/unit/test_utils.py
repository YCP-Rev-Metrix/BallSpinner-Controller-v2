import io
import builtins
import numpy as np
import pytest

import utils


class DummyParent:
    def __init__(self):
        # supply some colors so we can verify propagation
        self.accxColor = '#111111'
        self.motorRPMColor = '#222222'


def test_get_series_defs_uses_parent_colors():
    parent = DummyParent()
    defs = utils.get_series_defs(parent)
    # smartdot accel_x should have the parent's accxColor
    assert defs['smartdot']['accel_x']['color'] == '#111111'
    # motor series should pick up motorRPMColor
    assert defs['motor']['motor_rpm']['color'] == '#222222'


def test_series_arrays_returns_numpy_arrays():
    class Pkg:
        def __init__(self):
            self.time_rpm = [0, 1, 2]
            self.motor_rpm = [10, 20, 30]
    pkg = Pkg()
    defs = {'motor_rpm': {'time': 'time_rpm', 'data': 'motor_rpm'}}
    series = utils.series_arrays(pkg, defs)
    assert isinstance(series['motor_rpm'][0], np.ndarray)
    assert np.array_equal(series['motor_rpm'][1], np.array([10, 20, 30], dtype=np.float64))


def test_bandpass_wavelet_empty():
    arr = utils.bandpass_wavelet([])
    assert isinstance(arr, np.ndarray)
    assert arr.size == 0


def test_bandpass_wavelet_basic():
    vals = np.sin(np.linspace(0, 2 * np.pi, 32))
    out = utils.bandpass_wavelet(vals, wavelet='haar', level=2)
    assert out.shape == vals.shape
    # output should not be identical to input unless decomposition failed
    assert not np.allclose(out, vals)


def test_is_raspberry_pi_files(monkeypatch):
    # monkeypatch io.open used inside the utils module
    monkeypatch.setattr(utils.io, 'open', lambda path, mode='r': io.StringIO('Raspberry Pi Model B'))
    assert utils.is_raspberry_pi() is True
    assert utils.is_raspberry_pi_5() is False

    monkeypatch.setattr(utils.io, 'open', lambda path, mode='r': io.StringIO('Raspberry Pi 5'))
    assert utils.is_raspberry_pi_5() is True

    def raise_fn(path, mode='r'):
        raise FileNotFoundError
    monkeypatch.setattr(utils.io, 'open', raise_fn)
    assert utils.is_raspberry_pi() is False
    assert utils.is_raspberry_pi_5() is False


def test_notify_user(monkeypatch):
    # stub out QMessageBox to avoid GUI
    called = {}
    class FakeBox:
        class Icon:
            Warning = 1
            Critical = 2
            Information = 0
        def __init__(self):
            called['created'] = True
        def setIcon(self, icon):
            called['icon'] = icon
        def setWindowTitle(self, t):
            called['title'] = t
        def setText(self, t):
            called['text'] = t
        def setDetailedText(self, d):
            called['details'] = d
        def exec(self):
            called['executed'] = True
    monkeypatch.setattr(utils, 'QMessageBox', FakeBox)
    # provide dummy QApplication class that accepts args in constructor
    class FakeApp:
        def __init__(self, *args, **kwargs):
            pass
        @staticmethod
        def instance():
            return None
    monkeypatch.setattr(utils, 'QApplication', FakeApp)
    utils.notify_user('msg', title='tit', type='warning', details='dets')
    assert called['title'] == 'tit'
    assert called['text'] == 'msg'
    assert called['details'] == 'dets'
    assert called['executed']


def make_smartdot_entry(selector, **fields):
    obj = type('E', (), {'data_selector': selector, **fields})
    return obj


def test_PackageSmartDotData():
    class SD:
        def __init__(self):
            self.data_entries = []
    class DC:
        def __init__(self):
            self.smartdot_data = SD()
    class BSC:
        def __init__(self):
            self._dc = DC()
        def get_data_controller(self):
            return self._dc
    bsc = BSC()
    # add mixed entries to the single controller instance
    entry = make_smartdot_entry(0, time=0.1, accelerometer_x=1,
                                accelerometer_y=2, accelerometer_z=3,
                                gyroscope_x=4, gyroscope_y=5, gyroscope_z=6,
                                magnetometer_x=7, magnetometer_y=8, magnetometer_z=9,
                                light=10)
    bsc.get_data_controller().smartdot_data.data_entries.append(entry)
    # also add a light-only entry to exercise that branch
    light_entry = make_smartdot_entry(3, time=0.2, light=42)
    bsc.get_data_controller().smartdot_data.data_entries.append(light_entry)
    # use a dummy self object that allows attribute assignment
    dummy_self = type('DummySelf', (), {})()
    pkg = utils.PackageSmartDotData(dummy_self, bsc)
    # verify accelerometer data recorded and light data recorded
    assert pkg.accel_x[0] == 1
    assert pkg.light[0] == 42


def test_LegacyDiagnosticPacking_simple():
    time_rpm = []
    motor_rpm = []
    time_angle = []
    motor_angleDeg = []
    time_tilt = []
    motor_tiltDeg = []

    class D:
        def __init__(self, t, mid, instr):
            self.time = t
            self.motor_id = mid
            self.instruction = instr
    # simulate data at 0, 0.1, 0.2 all for rpm
    data = [D(0,0,10), D(0.1,0,20)]
    utils.LegacyDiagnosticPacking(data, time_rpm, motor_rpm, time_angle, motor_angleDeg, time_tilt, motor_tiltDeg, interval=0.1)
    assert motor_rpm[0] == 10
    assert motor_rpm[-1] == 20


def test_PackageMotorData_shot(monkeypatch):
    class SC:
        def __init__(self):
            self.isShotMode = True
    class DC:
        def __init__(self):
            self.session_data = SC()
            class MD:
                def get_shot_script_data_entries(self):
                    return [type('E', (), {'time':0, 'rpm':100,'angleDeg':1,'tiltDeg':2})]
            self.shot_script_data = MD()
    class BSC:
        diagnostic_sample_interval_ms = 50
        def get_data_controller(self):
            return DC()
    pkg = utils.PackageMotorData(BSC(), BSC()) if False else None
    # because the function signature is (self,bsc) but in utils it's defined as PackageMotorData(self,bsc)
    # it uses self as first argument but not used; call with dummy self
    result = utils.PackageMotorData(object(), BSC())
    assert hasattr(result, 'motor_rpm')
    assert result.motor_rpm[0] == 100
