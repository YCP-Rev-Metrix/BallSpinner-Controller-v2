from PyQt6 import QtWidgets, uic
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QTableView
from PyQt6.QtGui import QPixmap, QStandardItemModel, QStandardItem 
import os
from PyQt6.QtCore import pyqtSignal, QDateTime, QSortFilterProxyModel, Qt, QRegularExpression
from datetime import datetime, timezone
import datetime as dt
from BSC import bsc
from backend.models.DataController import DataController
from backend.models.SessionData import SessionData

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
        
        self.btnSearch.clicked.connect(
            lambda: self.refresh_data(self.dateStart.dateTime().toString("yyyyMMddhhmmss"), self.dateEnd.dateTime().toString("yyyyMMddhhmmss"))
            # lambda: print(int(self.dateStart.dateTime().toString("yyyyMMdd")))
            )
        
        #self.btnSearch.clicked.connect(self.refresh_data)
        self.btnAnalyze.clicked.connect(self.analyze_data)
        self.btnReplay.clicked.connect(self.replay_data)



        #Set Up dates 
        self.dateStart.setDateTime(QDateTime.currentDateTime().addDays(-7).addSecs(-7200))  # Default to one week  and 2 hrs ago
        self.dateEnd.setDateTime(QDateTime.currentDateTime().addSecs(7200))  # Default to 2 hrs from now
        
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


        # Use a custom proxy so we can combine text filtering with a session-type filter
        class FilterProxy(QSortFilterProxyModel):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.sessionTypeFilter = None  # None = any, True = shot, False = diagnostic

            def setSessionTypeFilter(self, value):
                self.sessionTypeFilter = value
                self.invalidateFilter()

            def filterAcceptsRow(self, source_row, source_parent):
                # First apply the base text filter behavior
                if not super().filterAcceptsRow(source_row, source_parent):
                    return False

                # If no session-type filter is set, accept
                if self.sessionTypeFilter is None:
                    return True

                model = self.sourceModel()
                # Find the column that contains the isShotMode (or isShot) header
                col = -1
                for c in range(model.columnCount()):
                    header = model.headerData(c, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
                    if header in ('isShotMode', 'isShot'):
                        col = c
                        break

                # If we couldn't find the column, don't filter it out
                if col == -1:
                    return True

                index = model.index(source_row, col, source_parent)
                data = str(model.data(index, Qt.ItemDataRole.DisplayRole)).strip().lower()
                if data in ('true', '1', 'yes'):
                    val = True
                elif data in ('false', '0', 'no'):
                    val = False
                else:
                    try:
                        val = bool(int(data))
                    except Exception:
                        return True

                return val == self.sessionTypeFilter

        self.proxy = FilterProxy(self)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)  # search all columns
        # make sure we filter on the displayed text
        self.proxy.setFilterRole(Qt.ItemDataRole.DisplayRole)
        # use a dedicated handler so user input is escaped and turned into a regex
        self.textSearch.textChanged.connect(self.on_search_text_changed)
        self.proxy.setSourceModel(self.model)
        self.tableview.setModel(self.proxy)

        # Ensure the combobox has the expected items (only add if not already present)
        if self.cboSessionType.count() == 0:
            self.cboSessionType.addItems(["All", "Diagnostic", "Shot"])

        # Connect combobox changes to update the proxy filter
        self.cboSessionType.currentTextChanged.connect(self.on_session_type_changed)
        # Initialize proxy filter from current combobox value
        self.on_session_type_changed(self.cboSessionType.currentText())

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

    def on_session_type_changed(self, text: str):
        t = text.strip().lower() if text else 'all'
        if t == 'all':
            self.proxy.setSessionTypeFilter(None)
        elif t.startswith('shot'):
            self.proxy.setSessionTypeFilter(True)
        elif t.startswith('diagnostic'):
            self.proxy.setSessionTypeFilter(False)
        else:
            self.proxy.setSessionTypeFilter(None)

    def refresh_data(self, start_time, end_time):
        print(start_time, end_time)
        # clear the persistent model and refill it; proxy filters this model
        self.model.clear()
        print(f"Getting sessions in time range: {start_time} to {end_time}")
        print(f"Type of start_time: {type(start_time)}, Type of end_time: {type(end_time)}")
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
                        item = QStandardItem(str(session[key]))
                        item.setEditable(False)
                        row.append(item)
                    self.model.appendRow(row)

        pass
    def load_data(self):
        #TODO: Implement data loading logic, turn session into Datacontroller with proper data
        sel = self.tableview.selectionModel().selectedRows()
        if not sel:
            return -1
        rowidx = self.proxy.mapToSource(sel[0])
        session_id_index = self.model.index(rowidx.row(), 0)  # Assuming first column is session ID
        session_id = int(self.model.data(session_id_index))
        timeStamp_index = self.model.index(rowidx.row(), 1)  # Assuming second column is timestamp
        timeStamp_str = self.model.data(timeStamp_index)
        name_index = self.model.index(rowidx.row(), 2)  # Assuming third column
        name_str = self.model.data(name_index)
        isShotMode_index = self.model.index(rowidx.row(), 3)  # Assuming
        isShotMode_str = self.model.data(isShotMode_index)
        isShotMode = isShotMode_str.strip().lower() in ('true', '1', 'yes')




        bsc.set_session(SessionData(id=session_id, timeStamp=timeStamp_str, name=name_str, isShotMode=isShotMode))
        bsc.set_data_controller(DataController(bsc.get_session()))
        bsc.get_data_controller().load_session_data_from_cloud(bsc.get_session())

        pass
    def analyze_data(self):
        print("Analyze Data Clicked")
        self.load_data()
        self.changePage.emit(3, bsc.get_data_controller())
        pass
    def replay_data(self):
        print("Replay Data Clicked")
        self.load_data()
        self.changePage.emit(6, bsc.get_data_controller())
        pass




        





if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = DataViewPage()
    window.show()
    sys.exit(app.exec())
