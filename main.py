from PyQt6 import QtWidgets
from logs.logger_config import setup_logging

from HomePage import HomePage

# Initialize logging at application startup
setup_logging()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = HomePage()
    window.show()
    QtWidgets.QApplication.exec()