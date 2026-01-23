from PyQt6 import QtWidgets
import pyqtgraph as pg
import numpy as np

pg.setConfigOptions(antialias=False)


class SensorGraphDialog(QtWidgets.QDialog):
    """
    Dialog window for displaying sensor graphs (temperature or current).
    
    HOW TO CREATE A POPUP DIALOG WITH MULTIPLE GRAPHS:
    
    1. Create a class that inherits from QtWidgets.QDialog
       - This gives you a popup window that can be shown with dialog.exec()
    
    2. In __init__, accept arrays of sensor data as parameters:
       - Time arrays (x-axis values)
       - Value arrays (y-axis sensor readings)
       - Labels for axes to customize the display
    
    3. Create a layout (QVBoxLayout or QGridLayout) to organize widgets:
       - QVBoxLayout stacks widgets vertically
       - QGridLayout arranges widgets in rows and columns
    
    4. Create PyQtGraph PlotWidget instances for each graph:
       - Each motor (spin, tilt, angle) gets its own plot
       - Set labels with setLabel() for axes
       - Plot data using plot() method with the time and value arrays
    
    5. Add graphs to a grid layout if displaying multiple side-by-side:
       - addWidget(widget, row, column) positions each graph
       - Multiple graphs give better visual comparison of data
    
    6. Add interactive widgets (buttons) for user control:
       - Connect button clicks to slots (methods like self.accept)
       - self.accept() closes the dialog when done
    
    7. Set the main layout with setLayout() to apply all widgets to the dialog
    """
    
    def __init__(self, title, spin_time, spin_values, tilt_time, tilt_values, 
                 angle_time, angle_values, y_label, parent=None):
        """
        Initialize the sensor graph dialog.
        
        Args:
            title: Title of the dialog window
            spin_time: Time array for spin data
            spin_values: Values array for spin data
            tilt_time: Time array for tilt data
            tilt_values: Values array for tilt data
            angle_time: Time array for angle data
            angle_values: Values array for angle data
            y_label: Label for the Y-axis
            parent: Parent widget
        """
        # Step 1: Initialize the dialog base class and set window properties
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 1200, 800)  # x, y, width, height
        
        # Step 2: Create main layout container
        layout = QtWidgets.QVBoxLayout(self)
        
        # Step 3: Create a container for the graph grid
        # (This would hold the grid layout with all three graphs)
        
        # Step 4: Create individual PlotWidget instances for each motor
        # (Each would have setLabel() for axes, plot() for data, and specific colors)
        
        # Step 5: Create a grid layout to arrange graphs side-by-side
        # (addWidget() places each graph in row/column positions)
        
        # Step 6: Add control button for closing the dialog
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)  # dialog.exec() will return
        layout.addWidget(close_btn)
        
        # Step 7: Apply the layout to make everything visible
        self.setLayout(layout)
