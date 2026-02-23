
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QHeaderView
from PyQt6.QtCore import Qt
import os
import pywt

class WavletHelperWidget(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'WavletHelperWidget.ui'), self)
        self.resize(1000, 1000)
        self.tblList.setColumnCount(5)
        self.tblList.setHorizontalHeaderLabels([
            "Family", "Type", "Order",
            "Isolate High-Frequency\n(Details)",
            "Isolate Low-Frequency\n(Approximation)"
        ])
        # make columns fill available space
        header = self.tblList.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # make the order column narrow since it only holds a spinbox; fix its width
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.tblList.setColumnWidth(2, 80)
        # determine row height based on styled combobox sizeHint
        # create temporary combobox offscreen to compute height; also configure its popup view for spacing
        sample_combo = QtWidgets.QComboBox()
        sample_view = QtWidgets.QListView()
        sample_view.setSpacing(20)
        sample_combo.setView(sample_view)
        sample_combo.setVisible(False)
        sample_height = sample_combo.sizeHint().height()
        self._row_height = sample_height + 80  # add buffer
        self.tblList.verticalHeader().setDefaultSectionSize(self._row_height)
        self.tblList.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tblList.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.AllEditTriggers)
        # Build a dict: family -> [types]
        # Map short family codes to long names
        self.family_long_names = {
            'haar': 'Haar',
            'db': 'Daubechies',
            'sym': 'Symlets',
            'coif': 'Coiflets',
            'bior': 'Biorthogonal',
            'rbio': 'Reverse Biorthogonal',
            'dmey': 'Discrete Meyer',
            'gaus': 'Gaussian',
            'mexh': 'Mexican Hat',
            'morl': 'Morlet',
            'cgau': 'Complex Gaussian',
            'shan': 'Shannon',
            'fbsp': 'Frequency B-Spline',
            'cmor': 'Complex Morlet',
        }
        self.wavelet_families = pywt.families()
        self.wavelet_types = {fam: pywt.wavelist(fam) for fam in self.wavelet_families}
        self.btnAddRow.clicked.connect(self.add_row)
        # duplicate and remove row buttons
        self.btnDuplicateRow.clicked.connect(self.duplicate_row)
        self.btnRemoveRow.clicked.connect(self.remove_row)
        self.btnPrev.clicked.connect(self.prev_item)
        self.btnNext.clicked.connect(self.next_item)
        self.btnOk.clicked.connect(self.accept)
        self.btnCancel.clicked.connect(self.reject)
        self.tblList.itemSelectionChanged.connect(self.update_index_label)
        self.current_row = 0
        self.update_index_label()


    def add_row(self, family=None, wtype=None, order=1,
                isolate_high=False, isolate_low=False, after_row: int | None = None):
        """Insert a new entry into the table.

        Parameters may be supplied to pre-populate the row; if none are
        provided defaults are used.  The row will be appended unless
        ``after_row`` specifies an index after which to insert (useful for
        duplicating the current selection).
        """
        # decide insertion position
        if after_row is None:
            row = self.tblList.rowCount()
        else:
            row = after_row
        self.tblList.insertRow(row)
        # Family ComboBox
        # use combo boxes whose popup is a list view with extra spacing
        family_combo = QtWidgets.QComboBox()
        fam_view = QtWidgets.QListView()
        fam_view.setSpacing(20)
        family_combo.setView(fam_view)
        for fam in self.wavelet_families:
            long_name = self.family_long_names.get(fam, fam)
            family_combo.addItem(long_name, fam)
        self.tblList.setCellWidget(row, 0, family_combo)
        # Type ComboBox
        type_combo = QtWidgets.QComboBox()
        type_view = QtWidgets.QListView()
        type_view.setSpacing(20)
        type_combo.setView(type_view)
        # choose initial family for types
        initial_fam = self.wavelet_families[0]
        type_combo.addItems(self.wavelet_types[initial_fam])
        self.tblList.setCellWidget(row, 1, type_combo)
        # Order spin box (integer exponent for dyadic scaling)
        order_spin = QtWidgets.QSpinBox()
        # change defaults to start at 1 (more intuitive for wavelet order)
        order_spin.setMinimum(1)
        order_spin.setMaximum(16)
        order_spin.setSingleStep(1)
        order_spin.setValue(order)
        order_spin.setFixedWidth(60)
        self.tblList.setCellWidget(row, 2, order_spin)
        # isolation checkboxes per row
        high_chk = QtWidgets.QCheckBox()
        low_chk = QtWidgets.QCheckBox()
        # center the checkboxes by placing them in a widget with centered layout
        high_container = QtWidgets.QWidget()
        low_container = QtWidgets.QWidget()
        # use a vertical layout with alignment to force full-row height
        v_layout_h = QtWidgets.QVBoxLayout(high_container)
        v_layout_h.setContentsMargins(0, 0, 0, 0)
        v_layout_h.addStretch()
        from PyQt6.QtCore import Qt as _QtConst
        v_layout_h.addWidget(high_chk, alignment=_QtConst.AlignmentFlag.AlignCenter)
        v_layout_h.addStretch()
        v_layout_l = QtWidgets.QVBoxLayout(low_container)
        v_layout_l.setContentsMargins(0, 0, 0, 0)
        v_layout_l.addStretch()
        v_layout_l.addWidget(low_chk, alignment=_QtConst.AlignmentFlag.AlignCenter)
        v_layout_l.addStretch()
        high_container.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                      QtWidgets.QSizePolicy.Policy.Expanding)
        low_container.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                     QtWidgets.QSizePolicy.Policy.Expanding)
        self.tblList.setCellWidget(row, 3, high_container)
        self.tblList.setCellWidget(row, 4, low_container)
        # Update type list when family changes
        def update_types():
            fam = family_combo.currentData()
            type_combo.clear()
            type_combo.addItems(self.wavelet_types[fam])
        family_combo.currentIndexChanged.connect(update_types)
        # apply passed-in values after widgets exist
        if family is not None:
            # select the matching family code
            index = family_combo.findData(family)
            if index != -1:
                family_combo.setCurrentIndex(index)
        if wtype is not None:
            # Qt will automatically update types when family changes so set
            # after the family selection above.
            idx = type_combo.findText(wtype)
            if idx != -1:
                type_combo.setCurrentIndex(idx)
        high_chk.setChecked(isolate_high)
        low_chk.setChecked(isolate_low)
        order_spin.setValue(order)
        # adjust row height after inserting the widgets so they fit correctly
        self.tblList.setRowHeight(row, self._row_height)
        self.tblList.selectRow(row)
        self.update_index_label()

    def remove_row(self):
        row = self.tblList.currentRow()
        if row >= 0:
            self.tblList.removeRow(row)
            self.update_index_label()

    def duplicate_row(self):
        """Create a copy of the currently selected row immediately below it."""
        row = self.tblList.currentRow()
        if row < 0:
            return
        data = self.get_list()[row]
        # insert after the current row, keeping same values
        self.add_row(
            family=data.get("family"),
            wtype=data.get("type"),
            order=data.get("order", 1),
            isolate_high=data.get("isolate_high", False),
            isolate_low=data.get("isolate_low", False),
            after_row=row + 1,
        )

    def prev_item(self):
        row = self.tblList.currentRow()
        if row > 0:
            self.tblList.selectRow(row - 1)
        self.update_index_label()

    def next_item(self):
        row = self.tblList.currentRow()
        if row < self.tblList.rowCount() - 1:
            self.tblList.selectRow(row + 1)
        self.update_index_label()

    def update_index_label(self):
        count = self.tblList.rowCount()
        row = self.tblList.currentRow()
        if count == 0:
            self.lblIndex.setText("0 / 0")
        else:
            self.lblIndex.setText(f"{row+1} / {count}")

    def get_list(self):
        result = []
        for row in range(self.tblList.rowCount()):
            family_combo = self.tblList.cellWidget(row, 0)
            type_combo = self.tblList.cellWidget(row, 1)
            order_widget = self.tblList.cellWidget(row, 2)
            # cell widgets may be containers; drill down to find checkboxes
            high_widget = self.tblList.cellWidget(row, 3)
            low_widget = self.tblList.cellWidget(row, 4)
            if family_combo and isinstance(family_combo, QtWidgets.QComboBox):
                family = family_combo.currentData()  # short code for pywt
                family_label = family_combo.currentText()  # long name for display
            else:
                family_item = self.tblList.item(row, 0)
                family = family_item.text() if family_item else ""
                family_label = family
            if type_combo and isinstance(type_combo, QtWidgets.QComboBox):
                wtype = type_combo.currentText()
            else:
                type_item = self.tblList.item(row, 1)
                wtype = type_item.text() if type_item else ""
            # order value
            order = 0
            if order_widget and isinstance(order_widget, QtWidgets.QSpinBox):
                order = order_widget.value()
            else:
                order_item = self.tblList.item(row, 2)
                if order_item:
                    try:
                        order = int(order_item.text())
                    except Exception:
                        order = 0
            # isolation flags per row: look for checkbox inside container
            isolate_high = False
            isolate_low = False
            def extract_chk(w):
                if isinstance(w, QtWidgets.QCheckBox):
                    return w
                if isinstance(w, QtWidgets.QWidget):
                    # search children for QCheckBox
                    for child in w.findChildren(QtWidgets.QCheckBox):
                        return child
                return None
            chk_h = extract_chk(high_widget)
            chk_l = extract_chk(low_widget)
            if chk_h is not None:
                isolate_high = chk_h.isChecked()
            if chk_l is not None:
                isolate_low = chk_l.isChecked()
            result.append({"family": family, "family_label": family_label, "type": wtype, "order": order,
                          "isolate_high": isolate_high, "isolate_low": isolate_low})
        return result


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    # apply global stylesheet if available
    try:
        style_path = os.path.join(os.path.dirname(__file__), "style.qss")
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    except Exception:
        pass

    dlg = WavletHelperWidget()
    if dlg.exec():
        print("Accepted. List:", dlg.get_list())
    else:
        print("Cancelled.")
