from PyQt6 import QtWidgets, uic, QtCore
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QTableView
from PyQt6.QtGui import QPixmap, QStandardItemModel, QStandardItem 
import os
from PyQt6.QtCore import pyqtSignal, QDateTime, QDate, QTime, QSortFilterProxyModel, Qt, QRegularExpression
from datetime import datetime, timezone
import datetime as dt
from BSC import bsc
from backend.models.DataController import DataController
from backend.models.SessionData import SessionData
from frontend.LoadingOverlay import LoadingOverlay
from utils import notify_user

class DataViewPage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object)

    

    def __init__(self, parent=None):
        super().__init__(parent)
        # load the .ui file (module-relative path)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'DataViewPage.ui'), self, package='frontend')

        self.rowIndex = -1
        self.row_data = []
        self.model = QStandardItemModel()
        self._cached_sessions = {}

        self.cloud_api = bsc.get_cloud_api()


        self.tableview = self.findChild(QtWidgets.QTableView, 'tblData')

        self.btnViewAll = self.findChild(QtWidgets.QPushButton, 'btnViewAll')
        self.btnSearch = self.findChild(QtWidgets.QPushButton, 'btnSearch')
        self.btnAnalyze = self.findChild(QtWidgets.QPushButton, 'btnAnalyze')
        self.btnReplay = self.findChild(QtWidgets.QPushButton, 'btnReplay')
        self.btnEdit = self.findChild(QtWidgets.QPushButton, 'btnEdit')
    


        self.textSearch = self.findChild(QtWidgets.QLineEdit, 'txtSearch')

        self.dateStartDate = self.findChild(QtWidgets.QDateEdit, 'dateStartDate')
        self.timeStartTime = self.findChild(QtWidgets.QTimeEdit, 'timeStartTime')
        self.dateEndDate = self.findChild(QtWidgets.QDateEdit, 'dateEndDate')
        self.timeEndTime = self.findChild(QtWidgets.QTimeEdit, 'timeEndTime')
        
        
        # Make calendar popup larger by setting cell dimensions
        self.dateStartDate.setCalendarPopup(True)
        self.dateEndDate.setCalendarPopup(True)
        start_calendar = self.dateStartDate.calendarWidget()
        end_calendar = self.dateEndDate.calendarWidget()
        if start_calendar is not None:
            start_calendar.setMinimumSize(600, 500)
        if end_calendar is not None:
            end_calendar.setMinimumSize(600, 500)

        self.cboSessionType = self.findChild(QtWidgets.QComboBox, 'cboSessionType')

        # Set time pickers to increment by 15 minutes
        self.timeStartTime.setDisplayFormat("hh:mm")
        self.timeStartTime.setCurrentSection(QtWidgets.QDateTimeEdit.Section.MinuteSection)
        from PyQt6.QtCore import QTime
        self.timeStartTime.setTime(QTime(0, 0))
        self.timeStartTime.setMinimumTime(QTime(0, 0))
        self.timeStartTime.setMaximumTime(QTime(23, 59))
        # Create a custom step for 15-minute increments
        self.timeStartTime.setWrapping(True)
        self.timeStartTime.stepBy = lambda steps: self._step_by_15_minutes(self.timeStartTime, steps)
        
        self.timeEndTime.setDisplayFormat("hh:mm")
        self.timeEndTime.setCurrentSection(QtWidgets.QDateTimeEdit.Section.MinuteSection)
        self.timeEndTime.setTime(QTime(0, 0))
        self.timeEndTime.setMinimumTime(QTime(0, 0))
        self.timeEndTime.setMaximumTime(QTime(23, 59))
        self.timeEndTime.setWrapping(True)
        self.timeEndTime.stepBy = lambda steps: self._step_by_15_minutes(self.timeEndTime, steps)

        # Connect button signals to their respective functions
        self.btnSearch.clicked.connect(
            lambda: self.refresh_data(
                self.dateStartDate.date().toString("yyyyMMdd") + self.timeStartTime.time().toString("hhmmss"),
                self.dateEndDate.date().toString("yyyyMMdd") + self.timeEndTime.time().toString("hhmmss")
            )
            )
        self.btnViewAll.clicked.connect(lambda: self.refresh_data("", ""))
        
        #self.btnSearch.clicked.connect(self.refresh_data)
        self.btnAnalyze.clicked.connect(self.analyze_data)
        self.btnReplay.clicked.connect(self.replay_data)
        self.btnEdit.clicked.connect(self.edit_data)



        #Set Up dates 
        current_datetime = QDateTime.currentDateTime()
        one_week_ago = current_datetime.addDays(-7).addSecs(-7200)  # One week and 2 hrs ago
        two_hours_future = current_datetime.addSecs(7200)  # 2 hrs from now
        
        # Round start time down to nearest 15 minutes
        start_time = one_week_ago.time()
        start_mins = start_time.minute()
        rounded_start_mins = (start_mins // 15) * 15
        rounded_start_time = QTime(start_time.hour(), rounded_start_mins, 0)
        
        # Round end time up to nearest 15 minutes
        end_time = two_hours_future.time()
        end_mins = end_time.minute()
        rounded_end_mins = ((end_mins + 14) // 15) * 15
        if rounded_end_mins >= 60:
            rounded_end_time = QTime((end_time.hour() + 1) % 24, 0, 0)
            if end_time.hour() == 23:
                two_hours_future = two_hours_future.addDays(1)
        else:
            rounded_end_time = QTime(end_time.hour(), rounded_end_mins, 0)
        
        self.dateStartDate.setDate(one_week_ago.date())
        self.timeStartTime.setTime(rounded_start_time)
        self.dateEndDate.setDate(two_hours_future.date())
        self.timeEndTime.setTime(rounded_end_time)
        
        # Set up the table model
        self.tableview.setSortingEnabled(True)
        self.tableview.resizeRowsToContents()
        self.tableview.resizeColumnsToContents()
        self.tableview.setWordWrap(True)
        self.tableview.resizeColumnsToContents()
        self.tableview.resizeRowsToContents()
        self.tableview.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableview.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.tableview.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tableview.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tableview.horizontalHeader().setStretchLastSection(True)
        self.tableview.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.tableview.verticalHeader().setDefaultSectionSize(50)  # Minimum row height for touch
        self.tableview.verticalHeader().setMinimumSectionSize(50)
        self.tableview.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.tableview.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

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
        # Use UserRole for sorting so it uses correct data types
        self.proxy.setSortRole(Qt.ItemDataRole.UserRole)
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

    def _step_by_15_minutes(self, time_edit, steps):
        """Helper method to step time by 15-minute increments"""
        current_time = time_edit.time()
        current_section = time_edit.currentSection()
        
        if current_section == QtWidgets.QDateTimeEdit.Section.MinuteSection:
            # Step by 15 minutes
            new_time = current_time.addSecs(steps * 15 * 60)
            time_edit.setTime(new_time)
        elif current_section == QtWidgets.QDateTimeEdit.Section.HourSection:
            # Step by 1 hour when in hour section
            new_time = current_time.addSecs(steps * 60 * 60)
            time_edit.setTime(new_time)

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
        #print(start_time, end_time)
        # clear the persistent model and refill it; proxy filters this model
        self.model.clear()
        #print(f"Getting sessions in time range: {start_time} to {end_time}")
        #print(f"Type of start_time: {type(start_time)}, Type of end_time: {type(end_time)}")

        QtWidgets.QApplication.processEvents()  # Force UI update before blocking call

        result = self.cloud_api.get_sessions_in_time_range(start_time, end_time)

        #Implement Error catching here
        if 'error' in result:
            notify_user("Failed to fetch data from the cloud. Please check your internet connection and try again.", title="No Data Found", type="critical", details=result['error'])


        #Implement data parsing here
        if result['status_code'] == 200:
            sessions = result['data']
            # cache sessions so we can retrieve full details (including instruction points) later
            self._cached_sessions = {int(s['id']): s for s in sessions if 'id' in s}
            print(f"Sessions: {sessions}")
            if len(sessions) > 0:
                # Set headers explicitly
                self.model.setHorizontalHeaderLabels(["id", "timestamp", "name", "isShotMode"])

                for session in sessions:
                    row = []
                    # 1. ID (int)
                    id_item = QStandardItem(str(session['id']))
                    id_item.setData(int(session['id']), Qt.ItemDataRole.UserRole)
                    id_item.setEditable(False)
                    row.append(id_item)

                    # 2. Timestamp (QDateTime)
                    ts_item = QStandardItem(session['timeStamp'])
                    dt = QDateTime.fromString(session['timeStamp'], "yyyy-MM-dd HH:mm:ss")
                    ts_item.setData(dt, Qt.ItemDataRole.UserRole)
                    ts_item.setEditable(False)
                    row.append(ts_item)

                    # 3. Name (string)
                    name_item = QStandardItem(session['name'])
                    name_item.setEditable(False)
                    row.append(name_item)

                    # 4. Is Shot Mode (bool)
                    shot_item = QStandardItem("Yes" if session['isShotMode'] else "No")
                    shot_item.setData(bool(session['isShotMode']), Qt.ItemDataRole.UserRole)
                    shot_item.setEditable(False)
                    row.append(shot_item)

                    # 5. Instruction points could be added as hidden columns if needed for sorting/filtering, but we'll keep them in the cache for now to avoid cluttering the UI
                    spin_points_item = QStandardItem(session['spin_Instruction_Points'])
                    spin_points_item.setEditable(False)
                    row.append(spin_points_item)

                    tilt_points_item = QStandardItem(session['tilt_Instruction_Points'])
                    tilt_points_item.setEditable(False)
                    row.append(tilt_points_item)

                    angle_points_item = QStandardItem(session['angle_Instruction_Points'])
                    angle_points_item.setEditable(False)
                    row.append(angle_points_item)
                    self.model.appendRow(row)
            else:
                notify_user("No sessions found in the specified time range, please adjust your filters and try again.", title="No Data Found", type="info")
            #hide instruction points columns for now since we don't want to display them, but we can use them for sorting/filtering if needed
            self.tableview.setColumnHidden(4, True)
            self.tableview.setColumnHidden(5, True)
            self.tableview.setColumnHidden(6, True)
    def load_data(self):
        
        sel = self.tableview.selectionModel().selectedRows()
        if not sel:
            notify_user("Please select a session to load.", title="No Session Selected", type="warning")
            return -1
        rowidx = self.proxy.mapToSource(sel[0])
        session_id_index = self.model.index(rowidx.row(), 0) 
        session_id = int(self.model.data(session_id_index))
        timeStamp_index = self.model.index(rowidx.row(), 1) 
        timeStamp_str = self.model.data(timeStamp_index)
        name_index = self.model.index(rowidx.row(), 2)  
        name_str = self.model.data(name_index)
        isShotMode_index = self.model.index(rowidx.row(), 3)  
        isShotMode_str = self.model.data(isShotMode_index)
        isShotMode = isShotMode_str.strip().lower() in ('true', '1', 'yes')
        spinPoinrts_index = self.model.index(rowidx.row(), 4)
        spin_points_str = self.model.data(spinPoinrts_index)
        spin_points = SessionData.string_to_instruction_points(spin_points_str)
        tilt_points_index = self.model.index(rowidx.row(), 5)
        tilt_points_str = self.model.data(tilt_points_index)
        tilt_points = SessionData.string_to_instruction_points(tilt_points_str)
        angle_points_index = self.model.index(rowidx.row(), 6)
        angle_points_str = self.model.data(angle_points_index)
        angle_points = SessionData.string_to_instruction_points(angle_points_str)

        bsc.set_session(SessionData(
            id=session_id,
            timeStamp=timeStamp_str,
            name=name_str,
            isShotMode=isShotMode,
            Spin_Instruction_Points=spin_points,
            Angle_Instruction_Points=angle_points,
            Tilt_Instruction_Points=tilt_points,
        ))
        bsc.set_data_controller(DataController(bsc.get_session()))
        bsc.get_data_controller().load_session_data_from_cloud(bsc.get_session())

       



    def analyze_data(self):
        print("Analyze Data Clicked")
        if(self.load_data() == -1):
            return
        self.changePage.emit(3, bsc.get_data_controller())
       
    def replay_data(self):
        print("Replay Data Clicked")
        if(self.load_data() == -1):
            return
        self.changePage.emit(6, bsc.get_data_controller())
    
    def edit_data(self):
        print("Edit Data Clicked")
        overlay = self._get_loading_overlay()
        overlay.show_message("Loading shot edit data...")
        try:
            if(self.load_data() == -1):
                return
            self.changePage.emit(2, bsc.get_data_controller())
        finally:
            # Keep it visible long enough for page transition/render to start.
            QtCore.QTimer.singleShot(150, overlay.hide_overlay)

    def _get_loading_overlay(self):
        host = self.window() or self
        overlay = getattr(host, "_global_loading_overlay", None)
        if overlay is None:
            overlay = LoadingOverlay(host)
            setattr(host, "_global_loading_overlay", overlay)
        return overlay
       




        





if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = DataViewPage()
    window.show()
    sys.exit(app.exec())
