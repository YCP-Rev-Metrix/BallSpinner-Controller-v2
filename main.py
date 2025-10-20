import sys
import numpy as np
import pyqtgraph as pg
import threading
import time
from PyQt6 import QtWidgets, uic

class MyGraphWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load the UI file.
        uic.loadUi('POC.ui', self)

        # Helper to get a widget by attribute name, then by findChild
        def _get_widget(cls, name):
            w = getattr(self, name, None)
            if w is None:
                try:
                    w = self.findChild(cls, name)
                except Exception:
                    w = None
            return w

        # Get references to the graph and dial widgets (robust lookup).
        self.graphs = [
            _get_widget(pg.PlotWidget, 'graph1'),
            _get_widget(pg.PlotWidget, 'graph2'),
            _get_widget(pg.PlotWidget, 'graph3')
        ]

        self.dials = [
            _get_widget(QtWidgets.QDial, 'dial'),
            _get_widget(QtWidgets.QDial, 'dial_2'),
            _get_widget(QtWidgets.QDial, 'dial_3')
        ]

        # If any widget is missing, create a reasonable fallback and insert
        # it into the central layout so the rest of the code can run.
        central = self.findChild(QtWidgets.QWidget, 'centralwidget') or self.centralWidget()
        layout = central.layout() if central is not None else None

        for i in range(len(self.graphs)):
            if self.graphs[i] is None:
                new_g = pg.PlotWidget()
                new_g.setObjectName(f'graph{i+1}')
                self.graphs[i] = new_g
                if layout is not None:
                    # attempt to place it in the same column as defined in the UI
                    layout.addWidget(new_g)
                else:
                    # as a last resort, set as central widget
                    self.setCentralWidget(new_g)

        for i in range(len(self.dials)):
            if self.dials[i] is None:
                new_d = QtWidgets.QDial()
                new_d.setObjectName(f'dial_{i+1}' if i > 0 else 'dial')
                self.dials[i] = new_d
                if layout is not None:
                    layout.addWidget(new_d)
        
        # Generate base data for the x-axis.
        self.x_data = np.linspace(0, 10, 500)
        
        # Store a reference to the plot lines so we can update them.
        self.plots = []
        
        # Call setup functions.
        self.setup_graphs()
        self.connect_dials()

        # Connect checkbox 'chkLockTab' to lock/unlock the tab topbar.
        try:
            self.chkLockTab = _get_widget(QtWidgets.QCheckBox, 'chkLockTab')
        except Exception:
            self.chkLockTab = None

        def _set_tab_lock(checked: bool):
            """Lock or unlock the QTabWidget's tab bar based on the checkbox state.

            When checked -> disable interactions on the tab bar (locked).
            When unchecked -> enable interactions (unlocked).
            """
            tab = _get_widget(QtWidgets.QTabWidget, 'tabWidget') or self.findChild(QtWidgets.QTabWidget, 'tabWidget')
            if tab is None:
                print('Warning: tabWidget not found; cannot lock tabs')
                return
            try:
                bar = tab.tabBar()
            except Exception:
                print('Warning: unable to access tabBar() on tabWidget')
                return

            # When checked, lock the bar (disable clicks/moves). Otherwise enable it.
            bar.setEnabled(not checked)

        # Ensure we have the checkbox reference (attribute or findChild) and connect.
        if self.chkLockTab is None:
            alt = self.findChild(QtWidgets.QCheckBox, 'chkLockTab')
            if alt is not None:
                self.chkLockTab = alt

        if self.chkLockTab is not None:
            self.chkLockTab.toggled.connect(_set_tab_lock)
            # Apply initial lock state immediately
            _set_tab_lock(self.chkLockTab.isChecked())

        # Start a background daemon thread that prints "hello world" every second
        # This uses time.sleep but won't block the GUI because it's running in a
        # separate daemon thread. We use an Event to signal shutdown on close.
        self._stop_event = threading.Event()

        def _printer():
            while not self._stop_event.is_set():
                print("hello world")
                time.sleep(1)

        t = threading.Thread(target=_printer, daemon=True)
        t.start()

    def setup_graphs(self):
        """Initializes each graph with a fixed range and disables user scaling."""
        for i, graph in enumerate(self.graphs):
            # Set titles and labels.
            graph.setTitle(f"Graph {i+1}")
            graph.setBackground('w')
            graph.setLabel('left', 'Amplitude')
            graph.setLabel('bottom', 'X-axis')

            # Lock the view to prevent auto-scaling and user scaling.
            graph.setXRange(0, 10, padding=0)
            graph.setYRange(-1.1, 1.1, padding=0)
            
            # Disable mouse interaction for zooming and panning.
            graph.setMouseEnabled(x=False, y=False)
            
            # Create the initial plot line and store its reference.
            plot_item = graph.plot(self.x_data, self.x_data * 0)
            self.plots.append(plot_item)
            
    def connect_dials(self):
        """Connects each dial's signal to its corresponding graph update slot."""
        for i, dial in enumerate(self.dials):
            # Set an initial value to make the lines visible on startup.
            dial.setValue(50)
            
            # Connect the valueChanged signal to the update function.
            # A lambda function is used to pass the index of the dial.
            dial.valueChanged.connect(lambda value, index=i: self.update_graph(index, value))
            
            # Call update_graph once at the start to draw the initial sine wave
            self.update_graph(i, dial.value())

    def update_graph(self, index, value):
        """Updates the plot data for a specific graph based on a dial's value."""
        # Scale the dial's value (0-99) to a suitable amplitude.
        amplitude = value / 99.0
        
        # Calculate the new y-data with the updated amplitude.
        y_data = amplitude * np.sin(self.x_data * 3 + index)
        
        # Update the plot line's data.
        self.plots[index].setData(self.x_data, y_data)

    def closeEvent(self, event):
        """Signal background threads to stop when the window is closing."""
        try:
            self._stop_event.set()
        except Exception:
            pass
        super().closeEvent(event)
        
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyGraphWindow()
    window.show()
    sys.exit(app.exec())