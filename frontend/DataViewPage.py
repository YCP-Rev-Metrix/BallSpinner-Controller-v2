from PyQt6 import QtWidgets, uic
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QTableView
from PyQt6.QtGui import QPixmap, QStandardItemModel, QStandardItem 
import os
from PyQt6.QtCore import pyqtSignal
from datetime import datetime, timezone
from BSC import bsc

class DataViewPage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object)

    

    def __init__(self, parent=None):
        super().__init__(parent)
        # load the .ui file (module-relative path)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'DataViewPage.ui'), self, package='frontend')

        self.rowIndex = -1
        self.row_data = []

        self.cloud_api = bsc.get_cloud_api()
        result = self.cloud_api.get_sessions_in_time_range(0,0)

        self.tableview = self.findChild(QtWidgets.QTableView, 'tableViewData')
        self.tableview.setSortingEnabled(True)
        self.tableview.resizeRowsToContents()
        self.tableview.resizeColumnsToContents()
        self.tableview.setWordWrap(True)
        self.tableview.clicked.connect(self.onRowSelected)

        self.btnSearch = self.findChild(QtWidgets.QPushButton, 'btnSearch')
        self.btnAnalyze = self.findChild(QtWidgets.QPushButton, 'btnAnalyze')
        self.btnReplay = self.findChild(QtWidgets.QPushButton, 'btnReplay')

        self.cboSessionType = self.findChild(QtWidgets.QComboBox, 'cboSessionType')

        # Connect button signals to their respective functions
        self.btnSearch.clicked.connect(self.refresh_data)
        self.btnAnalyze.clicked.connect(self.analyze_data)
        self.btnReplay.clicked.connect(self.replay_data)
        

        

        model = QStandardItemModel()

        if result['status_code'] == 200:
            sessions = result['data']
            if len(sessions) > 0:
                # Set headers
                headers = sessions[0].keys()
                model.setHorizontalHeaderLabels(headers)

                for session in sessions:
                    row = []
                    for key in headers:
                        if(session[key] is "timeStamp" ):
                            dt = datetime.fromtimestamp(session[key], tz=timezone.utc).astimezone()
                            item = QStandardItem(dt)
                        else:
                            item = QStandardItem(str(session[key]))
                        row.append(item)
                    model.appendRow(row)

        self.tableview.setModel(model)
        self.tableview.resizeColumnsToContents()
        self.tableview.resizeRowsToContents()
        self.tableview.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
    def refresh_data(self):
        print("Refresh Data Clicked")
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
    def onRowSelected(self, index):
        self.rowIndex = index.row()
        self.row_data = []
    # Iterate through all columns in the clicked row
        for column in range(self.tableview.model().columnCount()):
            self.cell_index = index.siblingAtColumn(column) 
            self.cell_data = self.tableview.model().data(self.cell_index)
            self.row_data.append(self.cell_data)
        print(f"Row {self.rowIndex} selected with data: {self.row_data}")




        





if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = DataViewPage()
    window.show()
    sys.exit(app.exec())
