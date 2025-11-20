from PyQt6 import QtWidgets, uic
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QTableView
from PyQt6.QtGui import QPixmap, QStandardItemModel, QStandardItem 
import os
from PyQt6.QtCore import pyqtSignal, QDateTime, QSortFilterProxyModel, Qt, QRegularExpression
from datetime import datetime, timezone
import datetime as dt
from BSC import bsc

class DataViewPage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object)

    

    def __init__(self, parent=None):
        super().__init__(parent)
        # load the .ui file (module-relative path)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'DataViewPage.ui'), self, package='frontend')

        self.rowIndex = -1
        self.row_data = []
        self.model = QStandardItemModel()

        self.cloud_api = bsc.get_cloud_api()


        self.tableview = self.findChild(QtWidgets.QTableView, 'tableViewData')



        self.btnSearch = self.findChild(QtWidgets.QPushButton, 'btnSearch')
        self.btnAnalyze = self.findChild(QtWidgets.QPushButton, 'btnAnalyze')
        self.btnReplay = self.findChild(QtWidgets.QPushButton, 'btnReplay')

        self.textSearch = self.findChild(QtWidgets.QLineEdit, 'txtSearch')

        self.dateStart = self.findChild(QtWidgets.QDateTimeEdit, 'dtStartTime')
        self.dateEnd = self.findChild(QtWidgets.QDateTimeEdit, 'dtEndTime')

        self.cboSessionType = self.findChild(QtWidgets.QComboBox, 'cboSessionType')

        # Connect button signals to their respective functions
        
        self.btnSearch.clicked.connect(lambda: self.refresh_data(
            int(self.dateStart.dateTime().toSecsSinceEpoch()),
            int(self.dateEnd.dateTime().toSecsSinceEpoch())
        ))
        
        #self.btnSearch.clicked.connect(self.refresh_data)
        self.btnAnalyze.clicked.connect(self.analyze_data)
        self.btnReplay.clicked.connect(self.replay_data)



        #Set Up dates 
        self.dateStart.setDateTime(QDateTime.currentDateTime().addDays(-7))  # Default to one week ago
        self.dateEnd.setDateTime(QDateTime.currentDateTime())  # Default to now
        
        # Set up the table model
        self.tableview.setSortingEnabled(True)
        self.tableview.resizeRowsToContents()
        self.tableview.resizeColumnsToContents()
        self.tableview.setWordWrap(True)
        self.tableview.resizeColumnsToContents()
        self.tableview.resizeRowsToContents()
        self.tableview.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableview.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.tableview.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tableview.horizontalHeader().setStretchLastSection(True)
        self.tableview.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.tableview.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)


        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)  # search all columns
        # make sure we filter on the displayed text
        self.proxy.setFilterRole(Qt.ItemDataRole.DisplayRole)
        # use a dedicated handler so user input is escaped and turned into a regex
        self.textSearch.textChanged.connect(self.on_search_text_changed)
        self.proxy.setSourceModel(self.model)
        self.tableview.setModel(self.proxy)

    def on_search_text_changed(self, text: str):
        # Escape the user input so regex metacharacters don't interfere,
        # then build a case-insensitive regex that matches anywhere in the cell text.
        if text:
            pattern = "(?i)" + QRegularExpression.escape(text)
            regex = QRegularExpression(pattern)
        else:
            regex = QRegularExpression()
        self.proxy.setFilterRegularExpression(regex)
        self.proxy.invalidate()

    def refresh_data(self, start_time: int = 0, end_time: int = 0):
        print(start_time, end_time)
        # clear the persistent model and refill it; proxy filters this model
        self.model.clear()
        result = self.cloud_api.get_sessions_in_time_range(start_time, end_time)
        if result['status_code'] == 200:
            sessions = result['data']
            if len(sessions) > 0:
                # Set headers
                headers = list(sessions[0].keys())
                self.model.setHorizontalHeaderLabels(headers)

                for session in sessions:
                    row = []
                    for key in headers:
                        if key == "timeStamp":
                            item = QStandardItem((QDateTime.fromSecsSinceEpoch(int(session[key])) if isinstance(session[key], (int, float)) or (isinstance(session[key], str) and session[key].isdigit()) else QDateTime.fromString(str(session[key]), Qt.DateFormat.ISODate)).toString(Qt.DateFormat.ISODate))
                        else:
                            item = QStandardItem(str(session[key]))
                        item.setEditable(False)
                        row.append(item)
                    self.model.appendRow(row)

        pass
    def load_data(self):
        #TODO: Implement data loading logic, turn session into Datacontroller with proper data
        pass
    def analyze_data(self):
        print("Analyze Data Clicked")
        self.load_data()
        self.changePage.emit(3, bsc.get_data_controller())
        pass
    def replay_data(self):
        print("Replay Data Clicked")
        self.changePage.emit(6, bsc.get_data_controller())
        pass




        





if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = DataViewPage()
    window.show()
    sys.exit(app.exec())
