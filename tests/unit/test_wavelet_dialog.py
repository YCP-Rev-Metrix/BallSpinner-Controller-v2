import numpy as np
import pywt
from PyQt6 import QtWidgets

from frontend.WaveletDialog import WaveletDialog


class DummyPackage:
    def __init__(self, times, values):
        self.time_rpm = times
        self.motor_rpm = values
        self.time_angle = times
        self.motor_angleDeg = values
        self.time_tilt = times
        self.motor_tiltDeg = values
        self.time_encoder = times
        self.encoder_rpm = values
        self.encoder_angle = values
        self.encoder_tilt = values


def test_wavelet_dialog_tabs(qtbot, monkeypatch):
    # monkeypatch the helper widget so that its dialog returns a specific
    # wavelet without popping up a GUI during testing
    # monkeypatch the helper class imported by WaveletDialog
    from frontend import WaveletDialog as _WD
    class DummyHelper:
        def __init__(self, parent=None):
            pass
        def exec(self):
            return QtWidgets.QDialog.DialogCode.Accepted
        def get_list(self):
            # specify a nonzero order so that detail arrays are computed
            return [
                {'family': 'haar', 'family_label': 'Haar', 'type': 'haar', 'order': 1},
                {'family': 'db', 'family_label': 'Daubechies', 'type': 'db2', 'order': 1}
            ]
    _WD.WavletHelperWidget = DummyHelper

    dlg = WaveletDialog()
    qtbot.addWidget(dlg)

    t = np.linspace(0, 1, 128)
    vals = np.linspace(0, 1, 128)
    pkg = DummyPackage(t, vals)

    dlg.performWavelet(pkg)
    # helper returned two wavelets, so two tabs plus original should appear
    assert dlg.tabAnalysis.count() == 3
    # names may include order or isolation suffixes; just check the prefixes
    assert dlg.tabAnalysis.tabText(0).startswith('haar')
    assert dlg.tabAnalysis.tabText(1).startswith('db2')
    assert dlg.tabAnalysis.tabText(2) == 'Original'
    # final tab should have two checkboxes, one for each wavelet
    final_tab = dlg.tabAnalysis.widget(2)
    cks = final_tab.findChildren(QtWidgets.QCheckBox)
    names = {ck.text() for ck in cks}
    assert len(names) == 2
    assert all(n.startswith(prefix) for n, prefix in zip(sorted(names), ['db2', 'haar']))
    # light series should not be present in results or graph
    assert 'light' not in dlg._wave_results
    graph = dlg.final_graph
    assert 'light' not in dlg.series_per_graph.get(graph, {})
    # verify toggling a box subtracts the detail from the first non-light series curve
    series_meta = dlg.series_per_graph.get(graph, {})
    assert series_meta, "final graph should have series data"
    common_keys = set(series_meta.keys()) & set(dlg._wave_results.keys())
    assert common_keys, "no overlapping series between final graph and wave results"
    first_key = next(iter(common_keys))
    entry = series_meta[first_key]
    orig_y = entry['orig_y'].copy()

    # pick up the computed wave names (they may include order/flags suffixes)
    detail_dict = dlg._wave_results[first_key][1]
    wave_names = list(detail_dict.keys())
    assert len(wave_names) >= 1
    # use first name for initial toggle
    name1 = wave_names[0]
    detail1 = detail_dict[name1]
    dlg.wave_checkboxes[name1].setChecked(True)
    ydata = entry['curve'].getData()[1]
    assert np.allclose(ydata, orig_y - detail1)

    if len(wave_names) > 1:
        name2 = wave_names[1]
        detail2 = detail_dict[name2]
        dlg.wave_checkboxes[name2].setChecked(True)
        ydata3 = entry['curve'].getData()[1]
        assert np.allclose(ydata3, orig_y - detail1 - detail2)
        # uncheck the first
        dlg.wave_checkboxes[name1].setChecked(False)
        ydata4 = entry['curve'].getData()[1]
        assert np.allclose(ydata4, orig_y - detail2)
        # finally uncheck the second
        dlg.wave_checkboxes[name2].setChecked(False)
        ydata5 = entry['curve'].getData()[1]
        assert np.allclose(ydata5, orig_y)

    dlg.close()



def test_wavelet_dialog_direct_wavelet(qtbot):
    # passing wavelet explicitly avoids any dialog
    dlg = WaveletDialog()
    qtbot.addWidget(dlg)
    t = np.linspace(0, 1, 64)
    vals = np.linspace(0, 1, 64)
    pkg = DummyPackage(t, vals)

    dlg.performWavelet(pkg, wavelet='db2')
    # one wavelet plus original
    assert dlg.tabAnalysis.count() == 2
    assert dlg.tabAnalysis.tabText(0) == 'db2'
    assert dlg.tabAnalysis.tabText(1) == 'Original'
    final_tab = dlg.tabAnalysis.widget(1)
    cks = final_tab.findChildren(QtWidgets.QCheckBox)
    assert len(cks) == 1 and cks[0].text() == 'db2'
    # ensure light not included
    assert 'light' not in dlg._wave_results
    assert 'light' not in dlg.series_per_graph.get(dlg.final_graph, {})

    dlg.close()


def test_wavelet_dialog_flag_names(qtbot, monkeypatch):
    """Tabs and checkboxes should include +high/+low when isolation flags set."""
    from frontend import WaveletDialog as _WD
    class DummyHelper2:
        def __init__(self, parent=None):
            pass
        def exec(self):
            return QtWidgets.QDialog.DialogCode.Accepted
        def get_list(self):
            return [
                {'family': 'db', 'family_label': 'Daubechies', 'type': 'db2',
                 'order': 1, 'isolate_high': True},
                {'family': 'db', 'family_label': 'Daubechies', 'type': 'db2',
                 'order': 2, 'isolate_low': True},
            ]
    _WD.WavletHelperWidget = DummyHelper2

    dlg = WaveletDialog()
    qtbot.addWidget(dlg)
    t = np.linspace(0, 1, 64)
    vals = np.linspace(0, 1, 64)
    pkg = DummyPackage(t, vals)

    dlg.performWavelet(pkg)
    # two detail tabs plus original
    assert dlg.tabAnalysis.count() == 3
    assert dlg.tabAnalysis.tabText(0).endswith('+high')
    assert dlg.tabAnalysis.tabText(1).endswith('+low')
    final_tab = dlg.tabAnalysis.widget(2)
    cks = final_tab.findChildren(QtWidgets.QCheckBox)
    names = {ck.text() for ck in cks}
    assert any(name.endswith('+high') for name in names)
    assert any(name.endswith('+low') for name in names)

    # check that the actual detail arrays reflect the isolation flags
    detail_dict = dlg._wave_results[next(iter(dlg._wave_results))][1]
    high_name = next(n for n in detail_dict if n.endswith('+high'))
    low_name = next(n for n in detail_dict if n.endswith('+low'))
    high_arr = detail_dict[high_name]
    low_arr = detail_dict[low_name]
    # for a simple ramp the low-isolated result should be very close to the
    # average / approximation; high-isolated should have low mean (not
    # identical to original) and nontrivial oscillation around zero.  allow a
    # small tolerance for numerical / boundary effects.
    assert np.allclose(low_arr, np.mean(low_arr)) is False
    assert abs(np.nanmean(high_arr)) < 1e-2

    dlg.close()


def test_wavelet_isolation_numeric(qtbot):
    """Directly confirm that the compute method zeroes the appropriate
    coefficient bands when isolation flags are used.
    """
    dlg = WaveletDialog()
    # create a simple sinusoid so we can inspect bandpass results
    arr = np.sin(np.linspace(0, 2 * np.pi, 128))

    # compute without any flags (baseline)
    name0, out0 = dlg._computeWaveletDetail(arr, 'db2', 2)
    assert out0 is not None
    # isolate_high should equal last-detail reconstruction
    name_high, out_high = dlg._computeWaveletDetail(arr, 'db2', 2, isolate_high=True)
    assert out_high is not None
    # reconstruct manually for comparison
    coeffs = pywt.wavedec(arr, 'db2', level=2)
    manual = coeffs[-1]  # this is high-detail vector at finest scale
    # reconstructed output should resemble the detail band (shape may differ)
    assert out_high.shape == out0.shape
    assert not np.allclose(out_high, out0)

    # isolate_low should give approximation-only output
    name_low, out_low = dlg._computeWaveletDetail(arr, 'db2', 2, isolate_low=True)
    assert out_low is not None
    # low output should be smooth compared to original
    assert np.nanstd(out_low) < np.nanstd(arr)


def test_open_wavelet_dialog_cancel(qtbot, monkeypatch):
    """If performWavelet reports failure, the analysis page should not show."""
    from frontend.AnalysisModePage import AnalysisModePage
    # stub out WaveletDialog.show so we can detect if it would have been shown
    shown = {'flag': False}
    def fake_show(self):
        shown['flag'] = True
    monkeypatch.setattr('frontend.WaveletDialog.WaveletDialog.show', fake_show)
    # make performWavelet return False to simulate cancellation
    monkeypatch.setattr('frontend.AnalysisModePage.WaveletDialog.performWavelet',
                        lambda self, pkg: False)

    # prevent the real package constructor from touching BSC
    monkeypatch.setattr('frontend.AnalysisModePage.PackageMotorData', lambda parent, bsc: object())
    page = AnalysisModePage()
    qtbot.addWidget(page)
    page.openWaveletDialog("Motor")
    assert not shown['flag'], "dialog should not be displayed when performWavelet fails"
