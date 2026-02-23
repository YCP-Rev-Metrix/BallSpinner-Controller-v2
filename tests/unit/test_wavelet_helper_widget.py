import pytest
from PyQt6 import QtWidgets
import numpy as np

from frontend.WavletHelperWidget import WavletHelperWidget


def test_helper_default_and_toggle(qtbot):
    dlg = WavletHelperWidget()
    qtbot.addWidget(dlg)

    assert dlg.tblList.rowCount() == 0
    dlg.add_row()
    assert dlg.tblList.rowCount() == 1
    result = dlg.get_list()
    assert isinstance(result, list) and len(result) == 1
    assert 'type' in result[0] and 'family' in result[0]
    # new default order should be 1
    assert result[0]['order'] == 1
    dlg.add_row()
    assert dlg.tblList.rowCount() == 2
    result = dlg.get_list()
    assert len(result) == 2


def test_duplicate_row(qtbot):
    helper = WavletHelperWidget()
    qtbot.addWidget(helper)
    # create a base row and populate with a non-default value so we can
    # easily verify duplication
    helper.add_row()
    first = helper.tblList.cellWidget(0, 2)
    assert isinstance(first, QtWidgets.QSpinBox)
    first.setValue(5)
    # duplicate the first row
    helper.tblList.selectRow(0)
    helper.duplicate_row()
    assert helper.tblList.rowCount() == 2
    lst = helper.get_list()
    assert lst[0] == lst[1], "duplicated row should have identical contents"


def test_helper_acceptance(qtbot):
    helper = WavletHelperWidget()
    qtbot.addWidget(helper)
    # nothing should crash when exec is called
    assert helper.exec() in (QtWidgets.QDialog.DialogCode.Accepted,
                               QtWidgets.QDialog.DialogCode.Rejected)
