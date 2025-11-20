from PyQt6 import QtWidgets, QtCore, uic
import os

class PostDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'PostDialog.ui'), self, package='frontend')
        self.buttonBox = self.findChild(QtWidgets.QDialogButtonBox, 'buttonBox')
        self.sessionNameInput = self.findChild(QtWidgets.QLineEdit, 'txtSessionName')

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