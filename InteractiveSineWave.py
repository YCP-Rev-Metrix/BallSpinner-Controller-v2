import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import Qt, QPointF
import numpy as np
import math

# Set up global application style (optional, but good for PyQTGraph)
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

class InteractiveSineWave(QtWidgets.QWidget):
    """
    A PyQt widget displaying a curve fixed at (0,0) and defined by a single 
    draggable peak point. The user clicks to set the peak's X position and 
    drags vertically to set its Y position (Amplitude).
    """
    def __init__(self, parent=None):
        # Allow uic/Qt to pass a parent when constructing the widget from .ui
        super().__init__(parent)
        
        # Create layout for this widget
        layout = QtWidgets.QVBoxLayout(self)
        
        # --- Plot Setup ---
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'Amplitude (Y)', units='A')
        self.plot_widget.setLabel('bottom', 'Phase (X)', units='rad')
        self.plot_widget.setTitle("Interactive Curve: Defined by Start (0,0) and Peak Point")
        self.plot_widget.showGrid(x=True, y=True)
        
        # Disable default pan/zoom functionality to allow custom dragging
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.hideButtons()
        
        # Create coordinate display label
        self.coord_label = QtWidgets.QLabel("Peak point: (0.00, 0.00)")
        self.coord_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; margin-top: 10px;")
        
        # Add widgets to layout
        layout.addWidget(self.plot_widget)
        layout.addWidget(self.coord_label)
        
        # --- Variables ---
        self.is_dragging = False
        self.inflection_x = np.pi / 2  # Default peak point X-position (mid-range)
        self.inflection_y = 300.0      # Default peak point Y-position (mid-amplitude)
        self.sine_curve_item = None
        self.point_item = None
        
        # Fixed start point (0, 0)
        self.fixed_point_x = 0.0
        self.fixed_point_y = 0.0
        
        # --- Initialization ---
        self.setup_sine_wave()
        
        # Connect custom mouse events to PlotWidget for drag control
        self.plot_widget.mousePressEvent = self.plot_mouse_press
        self.plot_widget.mouseMoveEvent = self.plot_mouse_move
        self.plot_widget.mouseReleaseEvent = self.plot_mouse_release
    
    def setup_sine_wave(self):
        """Generate and display the initial curve, set ranges, and place points."""
        
        # Generate x values from 0 to π (the full curve range)
        x = np.linspace(0, np.pi, 1000)
        y = self.generate_curve(x)
        
        # Plot the curve
        self.sine_curve_item = self.plot_widget.plot(
            x, y, pen=pg.mkPen(color='#3b82f6', width=3)
        )
        
        # Set axis limits
        self.plot_widget.setXRange(0, np.pi)
        self.plot_widget.setYRange(0, 600)
        
        # Place the initial draggable peak point
        self.place_draggable_point(self.inflection_x, self.inflection_y)
        
        # Add fixed point at (0,0) (Start of the curve)
        self.fixed_point_item = pg.ScatterPlotItem(
            [self.fixed_point_x], [self.fixed_point_y], 
            pen=pg.mkPen(color='green', width=2),
            brush=pg.mkBrush(color='green'),
            size=10,
            symbol='s'  # Square symbol for fixed point
        )
        self.plot_widget.addItem(self.fixed_point_item)

    def generate_curve(self, x):
        """
        Generate a smooth curve that starts at (0,0), peaks at (inflection_x, inflection_y), 
        and ends at (pi, 0). Uses two joined quarter-period sine waves.
        """
        if self.inflection_x <= 1e-6: # Handle case where peak X is near zero
            return np.zeros_like(x)
        
        # 1. Ascent Phase (0 < x <= inflection_x)
        # Goal: sin(B*inflection_x) = sin(pi/2) -> B = pi / (2 * inflection_x)
        ascent_mask = x <= self.inflection_x
        x_ascent = x[ascent_mask]
        
        # Scaled x for the ascent: goes from 0 to pi/2
        scaled_x_ascent = (x_ascent / self.inflection_x) * (np.pi / 2)
        y_ascent = np.sin(scaled_x_ascent) * self.inflection_y
        
        # 2. Descent Phase (inflection_x < x <= pi)
        # Goal: sin(C + D*descent_x) -> Starts at 1, ends at 0
        descent_mask = x > self.inflection_x
        x_descent = x[descent_mask]
        
        if len(x_descent) > 0:
            max_descent_x = np.pi - self.inflection_x
            
            # The descent segment must go from 0 to pi/2 in its internal scale
            # to make the sine function go from sin(pi/2)=1 to sin(pi)=0
            if max_descent_x > 1e-6:
                # Relative distance from the peak: goes from 0 to max_descent_x
                descent_x = x_descent - self.inflection_x
                
                # Scaled x for the descent: goes from 0 to pi/2
                scaled_x_descent = (descent_x / max_descent_x) * (np.pi / 2)
                
                # Curve: starts at sin(pi/2 + 0) = 1, ends at sin(pi/2 + pi/2) = 0
                y_descent = np.sin(np.pi / 2 + scaled_x_descent) * self.inflection_y
            else:
                y_descent = np.zeros_like(x_descent)
        
        # Combine the curves
        result = np.zeros_like(x)
        result[ascent_mask] = y_ascent
        if len(x_descent) > 0:
             result[descent_mask] = y_descent
        
        # Ensure values are within the vertical bounds (0 to 600)
        return np.maximum(0, np.minimum(600, result))
    
    # --- Custom Mouse Handlers ---
    
    def plot_mouse_press(self, event):
        """Handle mouse press: Sets the new X position of the peak point."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Get mouse position in plot coordinates
            pos = event.pos()
            mouse_point = self.plot_widget.getViewBox().mapSceneToView(QPointF(pos))
            x_click = mouse_point.x()
            y_click = mouse_point.y()
            
            # Constrain x to the visible range [0, pi]
            x_click = max(1e-6, min(np.pi, x_click)) # Use 1e-6 to avoid division by zero
            
            # Constrain y to valid range [0, 600]
            y_click = max(0, min(600, y_click))
            
            # Set the new inflection point position
            self.inflection_x = x_click
            self.inflection_y = y_click
            
            # Place or move the draggable point and start dragging
            self.place_draggable_point(self.inflection_x, self.inflection_y)
            self.is_dragging = True
            
            # Update the sine wave
            self.update_sine_wave()
        else:
            self.is_dragging = False
        
        # Accept the event to prevent default panning/zooming
        event.accept()

    def plot_mouse_move(self, event):
        """Handle mouse move: Allows vertical dragging (Y-only) when dragging is active."""
        if self.is_dragging:
            # Get mouse position in plot coordinates
            pos = event.pos()
            mouse_point = self.plot_widget.getViewBox().mapSceneToView(QPointF(pos))
            
            # Keep x position fixed, only allow y to change
            x_mouse = self.inflection_x
            y_mouse = mouse_point.y()
            
            # Constrain y to valid range [0, 600]
            y_mouse = max(0, min(600, y_mouse))
            
            # Update inflection point y-value
            self.inflection_y = y_mouse
            
            # Update point position and curve
            self.update_point_position(x_mouse, y_mouse)
            self.update_sine_wave()
        
        event.accept()

    def plot_mouse_release(self, event):
        """Handle mouse release: Stops dragging."""
        self.is_dragging = False
        event.accept()
    
    # --- UI Updaters ---

    def place_draggable_point(self, x, y):
        """Place a new draggable point at the specified coordinates."""
        # Remove existing point if any
        if self.point_item is not None:
            self.plot_widget.removeItem(self.point_item)
        
        # Create new point (Red circle)
        self.point_item = pg.ScatterPlotItem(
            [x], [y], 
            pen=pg.mkPen(color='red', width=2),
            brush=pg.mkBrush(color='red'),
            size=12,
            symbol='o'
        )
        self.plot_widget.addItem(self.point_item)
        
        self.update_coordinate_display(x, y)

    def update_point_position(self, x, y):
        """Update the position of the draggable point."""
        if self.point_item is not None:
            self.point_item.setData([x], [y])
            self.update_coordinate_display(x, y)

    def update_sine_wave(self):
        """Update the sine wave based on current peak point."""
        if self.sine_curve_item is not None:
            # Generate new x values
            x = np.linspace(0, np.pi, 1000)
            y = self.generate_curve(x)
            
            # Update the curve data
            self.sine_curve_item.setData(x, y)

    def update_coordinate_display(self, x, y):
        """Update the coordinate display label."""
        self.coord_label.setText(f"Peak point: ({x:.2f} rad, {y:.2f} A)")


if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show the main window
    window = InteractiveSineWave()
    window.setGeometry(100, 100, 800, 600) # x, y, width, height
    window.setWindowTitle("Interactive Curve Modeler")
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())
