from PyQt6 import QtWidgets, QtCore, uic
import os

class PostDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'PostDialog.ui'), self, package='frontend')
        self.buttonBox = self.findChild(QtWidgets.QDialogButtonBox, 'buttonBox')
        self.sessionNameInput = self.findChild(QtWidgets.QLineEdit, 'txtSessionName')

        # Accept touch events on dialog and its interactive children
        try:
            try:
                self.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
            except Exception:
                pass
            try:
                if self.buttonBox is not None:
                    self.buttonBox.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
            except Exception:
                pass
            try:
                if self.sessionNameInput is not None:
                    self.sessionNameInput.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
            except Exception:
                pass
        except Exception:
            pass

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.setWindowTitle("Save Data")
        self.setModal(True)
        self.resize(400, 200)
    
    def getSessionName(self):
        return self.sessionNameInput.text()

        


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    dialog = PostDialog()
    dialog.exec()