from PyQt6 import QtWidgets, uic
import pyqtgraph as pg
import numpy as np
import threading
import time

 


class HomePage(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load the UI file.
        uic.loadUi('HomePage.ui', self)
        
        tab = self.findChild(QtWidgets.QTabWidget, 'tabWidget')
        tab.currentChanged.connect(self.on_tab_changed)

        # The DiagnosticModePage is embedded as a promoted/custom widget in the UI.
        # In the HomePage.ui provided the objectName for that widget is likely 'widget_2' or 'DiagnosticModePage'.
        # Try to find it by the standard object name used in the UI.
        self.diagnosticPage = self.findChild(QtWidgets.QWidget, 'DiagnosticModePage')
        self.setFixedSize(1920, 1080)  # Set fixed window size to 1920x1080

       

    def on_tab_changed(self, index):
        # make sure diagnostic updates only run when the Diagnostic tab is selected
        # In HomePage.ui the Diagnostic Mode tab is usually index 0; adjust if different.
        is_diagnostic = (index == 0)
        diag = getattr(self, 'diagnosticPage', None)
        if diag is not None:
            # Prefer using the public setter if available
            if hasattr(diag, 'set_active'):
                try:
                    diag.set_active(is_diagnostic)
                except Exception:
                    # fallback: set attribute directly
                    setattr(diag, 'active', is_diagnostic)
            else:
                setattr(diag, 'active', is_diagnostic)

       

    def closeEvent(self, event):
        """Signal background threads to stop when the window is closing."""
        try:
            self._stop_event.set()
        except Exception:
            pass
        super().closeEvent(event)
        