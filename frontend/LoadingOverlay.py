from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import pyqtSignal


class LoadingOverlay(QtWidgets.QWidget):
    """Full-window dim overlay; Cancel dismisses the overlay and emits ``cancel_requested``."""

    cancel_requested = pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);")
        self.hide()

        panel = QtWidgets.QFrame(self)
        panel.setStyleSheet(
            "QFrame { background-color: #232629; border: 1px solid #3f4347; border-radius: 10px; }"
        )
        panel_layout = QtWidgets.QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 14, 16, 14)
        panel_layout.setSpacing(10)

        self.label = QtWidgets.QLabel("Loading...")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #f0f0f0; font-size: 11pt;")

        self.progress = QtWidgets.QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0)
        self.progress.setFixedWidth(220)

        panel_layout.addWidget(self.label)
        panel_layout.addWidget(self.progress, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        self.btn_cancel = QtWidgets.QPushButton("Cancel")
        self.btn_cancel.setStyleSheet(
            "QPushButton { color: #f0f0f0; background-color: #3f4347; "
            "border: 1px solid #5c6166; border-radius: 6px; padding: 6px 14px; font-size: 10pt; }"
            "QPushButton:hover { background-color: #5c6166; }"
        )
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        panel_layout.addWidget(self.btn_cancel, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch()
        row = QtWidgets.QHBoxLayout()
        row.addStretch()
        row.addWidget(panel)
        row.addStretch()
        outer.addLayout(row)
        outer.addStretch()

    def _on_cancel_clicked(self):
        self.cancel_requested.emit()
        self.hide_overlay()

    def resizeEvent(self, event):
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(parent.rect())
        super().resizeEvent(event)

    def show_message(self, message: str):
        self.label.setText(message)
        # Same busy indicator as initial state: indeterminate marquee (matches other loading calls).
        self.set_indeterminate()
        self.progress.setTextVisible(False)
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(parent.rect())
        self.raise_()
        self.show()

    def hide_overlay(self):
        self.hide()

    def set_indeterminate(self):
        """Marquee-style progress (unknown duration)."""
        self.progress.setRange(0, 0)

    def set_determinate(self, maximum: int):
        """Finite range ``0 .. maximum`` (inclusive)."""
        self.progress.setRange(0, max(0, int(maximum)))

    def set_progress_value(self, value: int):
        """Set completed amount (pairs with ``set_determinate`` maximum)."""
        self.progress.setValue(max(0, int(value)))

    def set_progress(self, value: int, maximum: int):
        """Set range and position in one call."""
        mx = max(1, int(maximum))
        self.progress.setRange(0, mx)
        self.progress.setValue(min(mx, max(0, int(value))))

    def set_progress_text_visible(self, visible: bool):
        """Show numeric ``x/y`` on the bar when determinate."""
        self.progress.setTextVisible(bool(visible))

