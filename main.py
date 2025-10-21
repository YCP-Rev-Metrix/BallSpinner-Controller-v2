from PyQt6 import QtWidgets

from HomePage import HomePage


count = 0

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = HomePage()
    window.show()
    QtWidgets.QApplication.exec()