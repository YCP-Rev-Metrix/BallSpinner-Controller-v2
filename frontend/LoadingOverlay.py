from PyQt6 import QtCore, QtWidgets


class LoadingOverlay(QtWidgets.QWidget):
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

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch()
        row = QtWidgets.QHBoxLayout()
        row.addStretch()
        row.addWidget(panel)
        row.addStretch()
        outer.addLayout(row)
        outer.addStretch()

    def resizeEvent(self, event):
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(parent.rect())
        super().resizeEvent(event)

    def show_message(self, message: str):
        self.label.setText(message)
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(parent.rect())
        self.raise_()
        self.show()

    def hide_overlay(self):
        self.hide()
