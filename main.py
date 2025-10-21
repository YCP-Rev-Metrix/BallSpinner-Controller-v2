from PyQt6 import QtWidgets

from HomePage import HomePage



if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = HomePage()
    window.show()
    QtWidgets.QApplication.exec()