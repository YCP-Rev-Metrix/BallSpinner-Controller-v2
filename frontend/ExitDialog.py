from PyQt6 import QtWidgets, uic
import os


class ExitDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ExitDialog.ui'), self)
        self.setWindowTitle("Confirm Exit")
        self.setModal(True)
        self.resize(400, 200)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.setWindowTitle("EXIT APPLICATION")
        self.setModal(True)
        self.resize(400, 200)

