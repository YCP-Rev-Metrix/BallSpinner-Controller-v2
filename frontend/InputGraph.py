from PyQt6 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np
import sys
import time

# Per-instance point storage (previously module-level globals) — removed globals below and
# use self.xPoints / self.yPoints so multiple InputGraph instances operate independently.

class InputGraph(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create layout for this widget
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        # --- Plot Setup ---
        self.plot_widget = pg.PlotWidget()
        # store axis label texts so units can be changed later via accessors
        self._y_label_text = 'Value'
        self._x_label_text = 'Time'
        self.plot_widget.setLabel('left', self._y_label_text, units='units')
        self.plot_widget.setLabel('bottom', self._x_label_text, units='units')
        self.plot_widget.setTitle("Input Graph")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.hideButtons()
        self.plot_widget.setXRange(0,1)
        self.plot_widget.setYRange(0,1)
        # -- header with clear button in top-right corner ---
        header = QtWidgets.QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)
        header.addStretch()
        # use a larger reset/refresh symbol for clarity
        self.clear_button = QtWidgets.QPushButton("↺")
        self.clear_button.setObjectName("btnInputGraphClear")
        # slightly larger circular red button so the symbol appears bigger
        # Use minimum and maximum sizes instead of fixed to allow scaling with parent
        self.clear_button.setMinimumSize(40, 40)
        self.clear_button.setMaximumSize(60, 60)
        # brief tooltip for clarity
        self.clear_button.setToolTip("Reset endpoints and clear points")
        # The clear button resets the view and clears points
        self.clear_button.clicked.connect(self.reset_view_and_clear)
        header.addWidget(self.clear_button)
        layout.addLayout(header)
        # Controls: endpoint Y values and degree (wrapped in a container so we can hide/show)
        controls_hbox = QtWidgets.QHBoxLayout()
        controls_hbox.setContentsMargins(0, 0, 0, 0)
        controls_hbox.setSpacing(12)

    # (degree control removed — spline degree is handled internally)

        # Start and End Y controls (float) constrained to [0,1]
        self.start_y_label = QtWidgets.QLabel("Start Value:")
        self.start_y_label.setMinimumWidth(90)
        self.start_y_spin = QtWidgets.QDoubleSpinBox()
        self.start_y_spin.setMinimumHeight(56)
        self.start_y_spin.setRange(0.0, 1.0)
        self.start_y_spin.setSingleStep(0.01)
        self.start_y_spin.setValue(0.0)
        self.start_y_spin.valueChanged.connect(self.onEndpointChanged)
        # Put start/end Y controls into their own container so they can be hidden separately
        self.endpoints_container = QtWidgets.QWidget()
        endpoints_layout = QtWidgets.QHBoxLayout()
        endpoints_layout.setContentsMargins(0, 0, 0, 0)
        endpoints_layout.setSpacing(0)
        start_group = QtWidgets.QVBoxLayout()
        start_group.setContentsMargins(0, 0, 0, 0)
        start_group.setSpacing(4)
        start_group.addWidget(self.start_y_label)
        start_group.addWidget(self.start_y_spin)

        self.end_y_label = QtWidgets.QLabel("End Value:")
        self.end_y_label.setMinimumWidth(90)
        self.end_y_spin = QtWidgets.QDoubleSpinBox()
        self.end_y_spin.setMinimumHeight(56)
        self.end_y_spin.setRange(0.0, 1.0)
        self.end_y_spin.setSingleStep(0.01)
        self.end_y_spin.setValue(0.0)
        self.end_y_spin.valueChanged.connect(self.onEndpointChanged)
        end_group = QtWidgets.QVBoxLayout()
        end_group.setContentsMargins(0, 0, 0, 0)
        end_group.setSpacing(4)
        end_group.addWidget(self.end_y_label)
        end_group.addWidget(self.end_y_spin)

        start_container = QtWidgets.QWidget()
        start_container.setLayout(start_group)
        end_container = QtWidgets.QWidget()
        end_container.setLayout(end_group)
        endpoints_layout.addWidget(start_container)
        endpoints_layout.addStretch()
        endpoints_layout.addWidget(end_container)

        self.endpoints_container.setLayout(endpoints_layout)
        # remember natural height
        if hasattr(self.endpoints_container, 'sizeHint'):
            self._endpoints_prev_height = self.endpoints_container.sizeHint().height()
        else:
            self._endpoints_prev_height = None

        # Y mapping controls (output scaling/shifting)
        self.ymin_label = QtWidgets.QLabel("Value min:")
        self.ymin_spin = QtWidgets.QDoubleSpinBox()
        self.ymin_spin.setMinimumHeight(56)
        self.ymin_spin.setRange(-10000.0, 10000.0)
        self.ymin_spin.setSingleStep(0.1)
        self.ymin_spin.setValue(0.0)
        self.ymin_spin.valueChanged.connect(self.onMappingChanged)
        controls_hbox.addWidget(self.ymin_label)
        controls_hbox.addWidget(self.ymin_spin)

        self.ymax_label = QtWidgets.QLabel("Value max:")
        self.ymax_spin = QtWidgets.QDoubleSpinBox()
        self.ymax_spin.setMinimumHeight(56)
        self.ymax_spin.setRange(-10000.0, 10000.0)
        self.ymax_spin.setSingleStep(0.1)
        self.ymax_spin.setValue(1.0)
        self.ymax_spin.valueChanged.connect(self.onMappingChanged)
        controls_hbox.addWidget(self.ymax_label)
        controls_hbox.addWidget(self.ymax_spin)

        # X mapping controls (output scaling). Constrained to [0,10]
        self.xmin_label = QtWidgets.QLabel("Time min:")
        self.xmin_spin = QtWidgets.QDoubleSpinBox()
        self.xmin_spin.setMinimumHeight(56)
        self.xmin_spin.setRange(0.0, 10.0)
        self.xmin_spin.setSingleStep(0.1)
        self.xmin_spin.setValue(0.0)
        self.xmin_spin.valueChanged.connect(self.onMappingChanged)
        controls_hbox.addWidget(self.xmin_label)
        controls_hbox.addWidget(self.xmin_spin)

        self.xmax_label = QtWidgets.QLabel("Time max:")
        self.xmax_spin = QtWidgets.QDoubleSpinBox()
        self.xmax_spin.setMinimumHeight(56)
        self.xmax_spin.setRange(0.0, 10.0)
        self.xmax_spin.setSingleStep(0.1)
        self.xmax_spin.setValue(1.0)
        self.xmax_spin.valueChanged.connect(self.onMappingChanged)
        controls_hbox.addWidget(self.xmax_label)
        controls_hbox.addWidget(self.xmax_spin)

        # Wrap controls in a container widget so they can be hidden/shown together
        controls_vbox = QtWidgets.QVBoxLayout()
        controls_vbox.setContentsMargins(0, 0, 0, 0)
        controls_vbox.setSpacing(6)
        controls_vbox.addLayout(controls_hbox)

        # Function display: show both unscaled (raw) and scaled (display) polynomials inside controls
        self.function_label_raw = QtWidgets.QLabel("raw f(u) = ")
        self.function_label_raw.setWordWrap(True)
        self.function_label_display = QtWidgets.QLabel("display f(x) = ")
        self.function_label_display.setWordWrap(True)
        # set selectable text interaction flag in a way that's compatible across PyQt6/5
        flags = None
        tif = getattr(QtCore.Qt, 'TextInteractionFlag', None)
        if tif is not None and hasattr(tif, 'TextSelectableByMouse'):
            flags = tif.TextSelectableByMouse
        elif hasattr(QtCore.Qt, 'TextSelectableByMouse'):
            flags = QtCore.Qt.TextSelectableByMouse
        if flags is not None:
            self.function_label_raw.setTextInteractionFlags(flags)
            self.function_label_display.setTextInteractionFlags(flags)
        controls_vbox.addWidget(self.function_label_raw)
        controls_vbox.addWidget(self.function_label_display)

        # (previously we displayed a compact numeric array here; removed per request)

        self.controls_container = QtWidgets.QWidget()
        self.controls_container.setLayout(controls_vbox)
        # remember current controls height for show/hide
        try:
            self._controls_prev_height = self.controls_container.sizeHint().height()
        except Exception:
            self._controls_prev_height = None
        # internal endpoint values
        # store endpoints internally as raw values in [0,1]
        self.start_y = float(self.start_y_spin.value())
        self.end_y = float(self.end_y_spin.value())
        # default endpoints (raw 0..1) used by reset; initialize to zeros by default
        # Callers may override via set_default_endpoints(...)
        self._default_start_y = 0.0
        self._default_end_y = 0.0

        # Initialize mapping attributes from spins
        self.xmin = float(self.xmin_spin.value())
        self.xmax = float(self.xmax_spin.value())
        self.ymin = float(self.ymin_spin.value())
        self.ymax = float(self.ymax_spin.value())

        # Set initial view ranges to mapped ranges
        self.plot_widget.setXRange(self.xmin, self.xmax)
        self.plot_widget.setYRange(self.ymin, self.ymax)

        # Ensure Start/End spinboxes reflect the mapped Y range and show mapped values
        # Safely set endpoint spin ranges and displayed values without duplicating
        # try/except blocks everywhere.
        self._safe_block(self.start_y_spin, True)
        self._safe_block(self.end_y_spin, True)
        self._safe_set_spin_range(self.start_y_spin, self.ymin, self.ymax)
        self._safe_set_spin_range(self.end_y_spin, self.ymin, self.ymax)
        # display mapped values corresponding to stored raw endpoints
        self._safe_set_spin_value(self.start_y_spin, self._map_y(self.start_y))
        self._safe_set_spin_value(self.end_y_spin, self._map_y(self.end_y))
        self._safe_block(self.start_y_spin, False)
        self._safe_block(self.end_y_spin, False)

        

        # Add plot widget to layout
        layout.addWidget(self.plot_widget)

        # (endpoints_container will be placed in the bottom row with Max points)

        # Add the controls container under the plot (below endpoints) so the plot
        # area remains the same height across multiple instances when controls
        # are shown/hidden.
        layout.addWidget(self.controls_container)

        # Max points control placed below the graph; insert endpoints into the same row
        bottom = QtWidgets.QHBoxLayout()
        bottom.setContentsMargins(12, 0, 12, 0)
        bottom.setSpacing(20)
        bottom.addStretch()
        bottom.addWidget(self.endpoints_container)
        bottom.addStretch()
        self.max_points_label = QtWidgets.QLabel("Max points:")
        self.max_points_label.setMinimumWidth(90)
        self.max_points_spin = QtWidgets.QSpinBox()
        self.max_points_spin.setMinimumHeight(56)
        self.max_points_spin.setRange(2, 1000)
        self.max_points_spin.setValue(10)
        self.max_points_spin.valueChanged.connect(self.onMaxPointsChanged)
        max_points_group = QtWidgets.QVBoxLayout()
        max_points_group.setContentsMargins(0, 0, 0, 0)
        max_points_group.setSpacing(4)
        max_points_group.addWidget(self.max_points_label)
        max_points_group.addWidget(self.max_points_spin)
        max_points_container = QtWidgets.QWidget()
        max_points_container.setLayout(max_points_group)
        bottom.addWidget(max_points_container)
        bottom.addStretch()
        layout.addLayout(bottom)

        # Initialize per-instance stored points (raw in [0,1])
        self.xPoints = []
        self.yPoints = []

        # Create two ScatterPlotItems for markers (left/right of piecewise split)
        # so we can color them differently.
        self.marker_scatter_left = pg.ScatterPlotItem(pen=pg.mkPen(None), brush='r', size=8)
        self.marker_scatter_right = pg.ScatterPlotItem(pen=pg.mkPen(None), brush='b', size=8)
        self.plot_widget.addItem(self.marker_scatter_left)
        self.plot_widget.addItem(self.marker_scatter_right)
        # Separate scatter for the configured endpoints (mapped & scaled) so they
        # are visible even when no user points exist.
        self.endpoint_scatter = pg.ScatterPlotItem(pen=pg.mkPen('w'), brush='g', size=10, symbol='s')
        self.plot_widget.addItem(self.endpoint_scatter)
        # Track the plotted curve so we can remove it between generations
        # support one or two plotted curves (non-piecewise: single; piecewise: two segments)
        self.curve_plots = []
        # (piecewise UI removed)

        # flag used to suppress single-click handling when a double-click was just handled
        self._suppress_next_click = False
        # Connect mouse click event (single-clicks handled here)
        self.plot_widget.scene().sigMouseClicked.connect(self.onClick)

        # Disable piecewise double-click behavior: do not install event filter for double-clicks
        self._graphics_view = None

        # Ensure widget starts in the reset state (apply defaults and clear points)
        self.reset_view_and_clear()
       

    def onClick(self, event):

        # Map the click position from scene coordinates to plot (data) coordinates
        scene_pos = event.scenePos()
        view_box = self.plot_widget.getViewBox()
        mouse_point = view_box.mapSceneToView(scene_pos)
        x = mouse_point.x()
        y = mouse_point.y()

        # First check if the click was on an existing marker (within a pixel threshold).
        # We compare in scene (pixel) coordinates so the tolerance is stable across scales.
        scene_click = event.scenePos()
        vb = self.plot_widget.getViewBox()
        remove_index = None
        threshold_px = 10.0
        for idx, (xx, yy) in enumerate(zip(self.xPoints, self.yPoints)):
            # xx,yy are stored raw in [0,1]; convert to mapped (display) coordinates for hit testing
            mapped_xx = self._map_x(xx)
            mapped_yy = self._map_y(yy)
            pt_scene = vb.mapViewToScene(QtCore.QPointF(float(mapped_xx), float(mapped_yy)))
            dist = ((pt_scene.x() - scene_click.x())**2 + (pt_scene.y() - scene_click.y())**2)**0.5
            if dist <= threshold_px:
                remove_index = idx
                break

        if remove_index is not None:
            # Single-click on a marker: delete that marker
            try:
                self.xPoints.pop(remove_index)
                self.yPoints.pop(remove_index)
            except Exception:
                pass

            # Update visuals and regenerate curve
            self._update_markers_mapped()
            self.generate_and_plot_curve()
            return


        # Not clicking an existing marker: add point (respect max points)
        # The view coordinates (x,y) are in mapped output ranges; convert back to raw [0,1]
        x_raw = self._unmap_x(x)
        y_raw = self._unmap_y(y)

        # Prevent adding points outside raw [0,1]
        if not (0.0 <= float(x_raw) <= 1.0 and 0.0 <= float(y_raw) <= 1.0):
            return

        maxp = getattr(self, 'max_points', self.max_points_spin.value())
        if len(self.xPoints) >= maxp:
            # At maximum points: do not accept new inputs. Provide a short beep as feedback.
            try:
                QtWidgets.QApplication.beep()
            except Exception:
                pass
            return

        # Store raw (0..1) values internally
        self.xPoints.append(x_raw)
        self.yPoints.append(y_raw)

        # Update scatter markers (mapped)
        self._update_markers_mapped()

        # Generate and plot the polynomial each click
        self.generate_and_plot_curve()
    def clearPlot(self):
        # Clear the plot and reset the global point lists
        # Clear the plot widget entirely and reset markers and lists
        self.plot_widget.clear()
        # Reset per-instance stored points
        self.xPoints = []
        self.yPoints = []
        # recreate marker and endpoint scatters using helper
        self.marker_scatter_left, self.marker_scatter_right, self.endpoint_scatter = self._create_marker_scatter()
        # (removed old piecewise visual cleanup - piecewise UI is no longer used)
        if self.endpoint_scatter is not None and hasattr(self.endpoints_container, 'isVisible') and not self.endpoints_container.isVisible():
            self.endpoint_scatter.hide()
        # clear remembered curve
        # remove any plotted curves
        try:
            for it in list(getattr(self, 'curve_plots', [])):
                try:
                    self.plot_widget.removeItem(it)
                except Exception:
                    pass
        except Exception:
            pass
        self.curve_plots = []
        # update labels safely (polynomial fields removed)
        self._safe_set_label(self.function_label_raw, "raw f(u) = ")
        self._safe_set_label(self.function_label_display, "display f(x) = ")

    def onMaxPointsChanged(self, val):
        # Called when spinbox changes. Trim existing stored points if necessary.
        self.max_points = int(val)
        while len(self.xPoints) > self.max_points:
            self.xPoints.pop(0)
            self.yPoints.pop(0)
        # Update markers to reflect trimming (mapped)
        self._update_markers_mapped()

    def onEndpointChanged(self, _val=None):
        """Called when either start or end Y spinbox changes."""
        # Spins display mapped (output) Y values; convert back to raw [0,1] for storage
        display_start = float(self.start_y_spin.value())
        display_end = float(self.end_y_spin.value())
        self.start_y = self._unmap_y(display_start)
        self.end_y = self._unmap_y(display_end)
        # regenerate curve with new endpoints
        self.generate_and_plot_curve()

    def onMappingChanged(self, _val=None):
        """Called when any mapping (x/y min/max) changes. Update view and regenerate curve."""
        # Enforce xmin/xmax bounds and ordering
        try:
            xmin = float(self.xmin_spin.value())
            xmax = float(self.xmax_spin.value())
        except Exception:
            xmin, xmax = 0.0, 1.0
        if xmin < 0.0:
            xmin = 0.0
        if xmax > 10.0:
            xmax = 10.0
        if xmax <= xmin:
            xmax = min(xmin + 1.0, 10.0)
        # Update spins if adjusted
        self.xmin_spin.blockSignals(True); self.xmin_spin.setValue(xmin); self.xmin_spin.blockSignals(False)
        self.xmax_spin.blockSignals(True); self.xmax_spin.setValue(xmax); self.xmax_spin.blockSignals(False)

        # Y mapping
        ymin = float(self.ymin_spin.value())
        ymax = float(self.ymax_spin.value())
        if ymax <= ymin:
            ymax = ymin + 1.0
        self.ymin_spin.blockSignals(True); self.ymin_spin.setValue(ymin); self.ymin_spin.blockSignals(False)
        self.ymax_spin.blockSignals(True); self.ymax_spin.setValue(ymax); self.ymax_spin.blockSignals(False)

        # Update current mapping attributes
        self.xmin, self.xmax = xmin, xmax
        self.ymin, self.ymax = ymin, ymax

        # Update view ranges to mapped ranges
        self.plot_widget.setXRange(self.xmin, self.xmax)
        self.plot_widget.setYRange(self.ymin, self.ymax)

        # Ensure the endpoint spinboxes' limits follow the new Y mapping
        # Safely update endpoint spin ranges and displayed values
        self._safe_block(self.start_y_spin, True)
        self._safe_block(self.end_y_spin, True)
        self._safe_set_spin_range(self.start_y_spin, self.ymin, self.ymax)
        self._safe_set_spin_range(self.end_y_spin, self.ymin, self.ymax)
        # keep displayed values in sync with stored raw endpoints
        self._safe_set_spin_value(self.start_y_spin, self._map_y(getattr(self, 'start_y', 0.0)))
        self._safe_set_spin_value(self.end_y_spin, self._map_y(getattr(self, 'end_y', 0.0)))
        self._safe_block(self.start_y_spin, False)
        self._safe_block(self.end_y_spin, False)

        # Remap existing markers and regenerate curve
        self._update_markers_mapped()
        self.generate_and_plot_curve()

    # Accessor methods for programmatic control
    def set_start_y(self, value: float):
        """Set the start Y endpoint value programmatically."""
        # Accept raw (0..1) value and update displayed spin to mapped coordinate
        try:
            raw = float(value)
        except Exception:
            return
        self.start_y = raw
        # Safely update displayed spin
        self._safe_set_spin_value(self.start_y_spin, self._map_y(raw))

    def set_end_y(self, value: float):
        """Set the end Y endpoint value programmatically."""
        # Accept raw (0..1) value and update displayed spin to mapped coordinate
        raw = float(value)
        self.end_y = raw
        # Safely update displayed spin
        self._safe_set_spin_value(self.end_y_spin, self._map_y(raw))

    # degree setter removed (degree control removed)

    def set_max_points(self, value: int):
        """Programmatically set the maximum stored points."""
        self.max_points_spin.setValue(int(value))

    def set_default_endpoints(self, start_raw: float, end_raw: float, apply_now: bool = False):
        """Set default start/end Y endpoints (raw values in [0,1]).

        If apply_now is True, the widget will update the current endpoints
        to the provided defaults immediately (and update the spinboxes/plot).
        Otherwise the defaults are stored and used the next time the reset
        button is pressed.
        """
        s = float(start_raw)
        e = float(end_raw)
        # clamp to [0,1]
        s = max(0.0, min(1.0, s))
        e = max(0.0, min(1.0, e))
        self._default_start_y = s
        self._default_end_y = e
        # Apply defaults immediately so callers (e.g. ShotModePage) see the
        # configured endpoints reflected without needing to call apply_now.
        # Apply new defaults and update displayed spins and plot safely
        self.start_y = s
        self.end_y = e
        self._safe_block(self.start_y_spin, True)
        self._safe_block(self.end_y_spin, True)
        self._safe_set_spin_value(self.start_y_spin, self._map_y(self.start_y))
        self._safe_set_spin_value(self.end_y_spin, self._map_y(self.end_y))
        self._safe_block(self.start_y_spin, False)
        self._safe_block(self.end_y_spin, False)
        # refresh markers and curve
        self._update_markers_mapped()
        self.generate_and_plot_curve()

    def get_default_endpoints(self):
        """Return a tuple (start_raw, end_raw) of the stored defaults (raw values 0..1)."""
        return (getattr(self, '_default_start_y', 0.0), getattr(self, '_default_end_y', 0.0))

    def set_bounds(self, xmin: float = None, xmax: float = None, ymin: float = None, ymax: float = None):
        """Programmatically set the mapping bounds for X and Y.

        Any argument left as None will keep its current value. Values are
        validated and clamped to the same rules as the UI: xmin>=0, xmax<=10,
        and xmax>xmin (otherwise xmax is set to xmin+1 limited to 10). For Y,
        ymax>ymin (otherwise ymax is set to ymin+1).

        This updates the spinboxes and then calls the existing mapping handler
        to apply the changes and regenerate the plot.
        """
        # Read current values (fallback to sensible defaults if widgets missing)
        cur_xmin = float(self.xmin_spin.value()) if hasattr(self, 'xmin_spin') else 0.0
        cur_xmax = float(self.xmax_spin.value()) if hasattr(self, 'xmax_spin') else 1.0
        cur_ymin = float(self.ymin_spin.value()) if hasattr(self, 'ymin_spin') else 0.0
        cur_ymax = float(self.ymax_spin.value()) if hasattr(self, 'ymax_spin') else 1.0

        # Determine targets (use provided or current)
        txmin = cur_xmin if xmin is None else float(xmin)
        txmax = cur_xmax if xmax is None else float(xmax)
        tymin = cur_ymin if ymin is None else float(ymin)
        tymax = cur_ymax if ymax is None else float(ymax)

        # Enforce bounds and ordering
        if txmin < 0.0:
            txmin = 0.0
        if txmax > 10.0:
            txmax = 10.0
        if txmax <= txmin:
            # try to expand xmax, otherwise clamp
            txmax = min(txmin + 1.0, 10.0)
            if txmax <= txmin:
                txmin = max(0.0, txmax - 1.0)

        if tymax <= tymin:
            tymax = tymin + 1.0

        # Apply to spinboxes without triggering intermediate handlers
        try:
            self.xmin_spin.blockSignals(True)
            self.xmax_spin.blockSignals(True)
            self.ymin_spin.blockSignals(True)
            self.ymax_spin.blockSignals(True)
            self.xmin_spin.setValue(txmin)
            self.xmax_spin.setValue(txmax)
            self.ymin_spin.setValue(tymin)
            self.ymax_spin.setValue(tymax)
        finally:
            try:
                self.xmin_spin.blockSignals(False)
                self.xmax_spin.blockSignals(False)
                self.ymin_spin.blockSignals(False)
                self.ymax_spin.blockSignals(False)
            except Exception:
                pass

        # Apply via the existing handler so all bookkeeping is done in one place
        try:
            self.onMappingChanged()
        except Exception:
            # fall back to manual assignment
            try:
                self.xmin, self.xmax = txmin, txmax
                self.ymin, self.ymax = tymin, tymax
                self.plot_widget.setXRange(self.xmin, self.xmax)
                self.plot_widget.setYRange(self.ymin, self.ymax)
                self._update_markers_mapped()
                self.generate_and_plot_curve()
            except Exception:
                pass

    def _map_x(self, x_raw: float) -> float:
        """Map raw x in [0,1] to output x using xmin/xmax."""
        xmin = getattr(self, 'xmin', 0.0)
        xmax = getattr(self, 'xmax', 1.0)
        return xmin + float(x_raw) * (xmax - xmin)

    def _map_y(self, y_raw: float) -> float:
        """Map raw y in [0,1] to output y using ymin/ymax."""
        ymin = getattr(self, 'ymin', 0.0)
        ymax = getattr(self, 'ymax', 1.0)
        return ymin + float(y_raw) * (ymax - ymin)

    

    def _unmap_x(self, x_mapped: float) -> float:
        """Inverse of _map_x: map displayed x back to raw [0,1].

        If xmin==xmax returns 0.0 to avoid division by zero.
        """
        xmin = getattr(self, 'xmin', 0.0)
        xmax = getattr(self, 'xmax', 1.0)
        try:
            if float(xmax) == float(xmin):
                return 0.0
            return (float(x_mapped) - float(xmin)) / (float(xmax) - float(xmin))
        except Exception:
            return 0.0

    def _unmap_y(self, y_mapped: float) -> float:
        """Inverse of _map_y: map displayed y back to raw [0,1].

        If ymin==ymax returns 0.0 to avoid division by zero.
        """
        ymin = getattr(self, 'ymin', 0.0)
        ymax = getattr(self, 'ymax', 1.0)
        try:
            if float(ymax) == float(ymin):
                return 0.0
            return (float(y_mapped) - float(ymin)) / (float(ymax) - float(ymin))
        except Exception:
            return 0.0

    # -- Small helpers to reduce repeated try/except and blockSignals patterns --
    def _safe_block(self, widget, flag: bool):
        try:
            widget.blockSignals(flag)
        except Exception:
            pass

    def _safe_set_spin_value(self, spin, val):
        try:
            spin.setValue(val)
        except Exception:
            pass

    def _safe_set_spin_range(self, spin, mn, mx):
        try:
            spin.setRange(mn, mx)
        except Exception:
            pass

    def _safe_set_label(self, label, txt):
        try:
            label.setText(txt)
        except Exception:
            pass

    def _safe_plot_set_range(self, xmin, xmax, ymin, ymax):
        try:
            self.plot_widget.setXRange(xmin, xmax)
            self.plot_widget.setYRange(ymin, ymax)
        except Exception:
            pass

    def _create_marker_scatter(self):
        """Create left/right marker scatters and endpoint scatter and add to the plot.

        Returns (marker_scatter_left, marker_scatter_right, endpoint_scatter).
        """
        ms_left = pg.ScatterPlotItem(pen=pg.mkPen(None), brush='r', size=8)
        ms_right = pg.ScatterPlotItem(pen=pg.mkPen(None), brush='b', size=8)
        es = None
        try:
            es = pg.ScatterPlotItem(pen=pg.mkPen('w'), brush='g', size=10, symbol='s')
        except Exception:
            try:
                es = pg.ScatterPlotItem(pen=pg.mkPen('w'), brush='g', size=10)
            except Exception:
                es = None
        try:
            self.plot_widget.addItem(ms_left)
            self.plot_widget.addItem(ms_right)
            if es is not None:
                self.plot_widget.addItem(es)
        except Exception:
            pass
        return ms_left, ms_right, es

    def eventFilter(self, obj, event):
        # Piecewise/double-click behavior disabled — pass through to default handler
        return super().eventFilter(obj, event)

    def _update_markers_mapped(self):
        """Update marker scatter using mapped coordinates."""
        mapped_x = [self._map_x(x) for x in self.xPoints]
        mapped_y = [self._map_y(y) for y in self.yPoints]
        # No piecewise behavior: show all markers in the single (left) scatter
        try:
            if getattr(self, 'marker_scatter_left', None) is not None:
                self.marker_scatter_left.setData(x=mapped_x, y=mapped_y)
            if getattr(self, 'marker_scatter_right', None) is not None:
                self.marker_scatter_right.setData(x=[], y=[])
        except Exception:
            pass
        # Also show the configured endpoints as scaled/mapped markers at x= xmin/xmax
        try:
            start_mx = self._map_x(0.0)
            end_mx = self._map_x(1.0)
            start_my = self._map_y(getattr(self, 'start_y', 0.0))
            end_my = self._map_y(getattr(self, 'end_y', 0.0))
            self.endpoint_scatter.setData(x=[start_mx, end_mx], y=[start_my, end_my])
            # toggle visibility to match the endpoints container
            try:
                if self.endpoints_container.isVisible():
                    self.endpoint_scatter.show()
                else:
                    self.endpoint_scatter.hide()
            except Exception:
                pass
        except Exception:
            try:
                self.endpoint_scatter.setData(x=[], y=[])
            except Exception:
                pass
        # (removed leftover piecewise visual hiding — not used anymore)

    def hide_controls(self):
        """Hide the graphical controls container (max points, start/end Y)."""
        try:
            # remember previous natural height so we can restore on show
            if not hasattr(self, '_controls_prev_height') or self._controls_prev_height is None:
                try:
                    self._controls_prev_height = self.controls_container.sizeHint().height()
                except Exception:
                    self._controls_prev_height = None
            # set height to zero and hide
            try:
                self.controls_container.setFixedHeight(0)
            except Exception:
                pass
            self.controls_container.hide()
        except Exception:
            pass

    def show_controls(self):
        """Show the graphical controls container."""
        self.controls_container.show()

    def hide_endpoints(self):
        """Hide the start/end Y controls container and set its height to zero."""
        self.endpoints_container.hide()
        
    def show_endpoints(self):
        """Show the start/end Y controls container and restore its height."""
        self.endpoints_container.show()
        

    def generate_and_plot_curve(self):
        """Fit and plot the curve for the current set of points.

        The method builds combined points including configured endpoints,
        generates a Hermite-style spline per interval, samples and plots it,
        and stores callables/interval structures used by the public accessors.
    The plotted curve(s) are stored in `self.curve_plots` for later removal.
        """
        # Build combined points (raw domain u in [0,1]) including endpoints
        pts = list(zip(self.xPoints, self.yPoints))
        start_y = float(getattr(self, 'start_y', 0.0))
        end_y = float(getattr(self, 'end_y', 0.0))
        pts.append((0.0, start_y))
        pts.append((1.0, end_y))
        # Deduplicate by x (rounded) and validate, ensuring unique x-values
        # Deduplicate by x (rounded) and validate
        dedup = {}
        for x, y in pts:
            key = round(float(x), 12)
            if key in dedup and abs(dedup[key] - float(y)) > 1e-8:
                # conflicting y for same x -> abort
                return
            dedup[key] = float(y)

        xs = np.array(sorted(dedup.keys()))
        ys = np.array([dedup[x] for x in xs])

        if xs.size < 2:
            # nothing to fit
            # remove any existing curves
            try:
                for it in list(getattr(self, 'curve_plots', [])):
                    try:
                        self.plot_widget.removeItem(it)
                    except Exception:
                        pass
            except Exception:
                pass
            self.curve_plots = []
            # clear labels (polynomial/piecewise fields removed)
            try:
                self.function_label_raw.setText("raw f(u) = ")
                self.function_label_display.setText("display f(x) = ")
            except Exception:
                pass
            # array label removed
            return

        # degree requested by user, capped per-segment later
        try:
            requested_deg = int(self.degree_spin.value()) if hasattr(self, 'degree_spin') else (xs.size - 1)
        except Exception:
            requested_deg = xs.size - 1

        # convenience mapping params
        xmin = float(getattr(self, 'xmin', 0.0))
        xmax = float(getattr(self, 'xmax', 1.0))
        ymin = float(getattr(self, 'ymin', 0.0))
        ymax = float(getattr(self, 'ymax', 1.0))

        # remove old plotted curves
        try:
            for it in list(getattr(self, 'curve_plots', [])):
                try:
                    self.plot_widget.removeItem(it)
                except Exception:
                    pass
        except Exception:
            pass
        self.curve_plots = []

        # Helper: construct a cubic Hermite spline (per-interval) and plot it.
        def hermite_fit_and_plot(x_vals, y_vals, color='b'):
            """Build monotonic cubic Hermite coefficients per interval and plot.

            Returns a tuple: (callable_raw, raw_intervals, display_intervals, disp_expr_str)
            - callable_raw(u) evaluates raw-domain spline at u in [0,1]
            - raw_intervals: list of [x0, h_raw, a,b,c,d] per interval (coeffs in local u)
            - display_intervals: list of [x0_disp, h_disp, a_disp,b_disp,c_disp,d_disp]
            - disp_expr_str: empty string (placeholder for compatibility)
            """
            if x_vals.size < 2:
                return None, [], [], ""
            # ensure sorted
            order = np.argsort(x_vals)
            x = np.asarray(x_vals)[order]
            y = np.asarray(y_vals)[order]
            n = x.size
            h = np.diff(x)
            delta = np.diff(y) / h

            # compute tangents m at nodes
            m = np.zeros(n, dtype=float)
            if n == 2:
                m[0] = m[1] = delta[0]
            else:
                m[0] = delta[0]
                m[-1] = delta[-1]
                for i in range(1, n - 1):
                    if delta[i - 1] == 0.0 or delta[i] == 0.0 or (delta[i - 1] < 0) != (delta[i] < 0):
                        m[i] = 0.0
                    else:
                        # average slopes weighted by interval lengths
                        m[i] = (h[i] * delta[i - 1] + h[i - 1] * delta[i]) / (h[i - 1] + h[i])

            # per-interval Hermite cubic coefficients in local u (0..1):
            # S(u) = a + b*u + c*u^2 + d*u^3, where u = (t - x_i)/h_i
            raw_intervals = []
            for i in range(n - 1):
                x0 = float(x[i])
                h_i = float(h[i])
                y0 = float(y[i])
                y1 = float(y[i + 1])
                m0 = float(m[i])
                m1 = float(m[i + 1])
                a = y0
                b = m0 * h_i
                c = -3 * y0 + 3 * y1 - 2 * m0 * h_i - m1 * h_i
                d = 2 * y0 - 2 * y1 + m0 * h_i + m1 * h_i
                raw_intervals.append([x0, h_i, a, b, c, d])

            # build display-domain intervals
            scale_x = (xmax - xmin) if (xmax - xmin) != 0 else 1.0
            scale_y = (ymax - ymin) if (ymax - ymin) != 0 else 1.0
            display_intervals = []
            for (x0, h_i, a, b, c, d) in raw_intervals:
                x0_disp = float(xmin + x0 * scale_x)
                h_disp = float(h_i * scale_x)
                a_disp = float(ymin + scale_y * a)
                b_disp = float(scale_y * b)
                c_disp = float(scale_y * c)
                d_disp = float(scale_y * d)
                display_intervals.append([x0_disp, h_disp, a_disp, b_disp, c_disp, d_disp])

            # Plot by sampling each interval
            try:
                for (x0, h_i, a, b, c, d) in raw_intervals:
                    us = np.linspace(0.0, 1.0, 200)
                    vals = a + b * us + c * us ** 2 + d * us ** 3
                    vals = np.clip(vals, 0.0, 1.0)
                    xs_plot = [self._map_x(x0 + u * h_i) for u in us]
                    ys_plot = [self._map_y(v) for v in vals]
                    try:
                        line = self.plot_widget.plot(xs_plot, ys_plot, pen=pg.mkPen(color, width=2))
                        self.curve_plots.append(line)
                    except Exception:
                        pass
            except Exception:
                pass

            # callable raw evaluator
            def raw_eval(u_query):
                # u_query in [0,1]
                uq = float(u_query)
                if uq <= x[0]:
                    return float(y[0])
                if uq >= x[-1]:
                    return float(y[-1])
                # find interval index
                idx = np.searchsorted(x, uq) - 1
                if idx < 0:
                    idx = 0
                if idx >= len(raw_intervals):
                    idx = len(raw_intervals) - 1
                x0_i, h_i, a, b, c, d = raw_intervals[idx]
                local_u = (uq - x0_i) / h_i if h_i != 0 else 0.0
                local_u = np.clip(local_u, 0.0, 1.0)
                return float(a + b * local_u + c * local_u ** 2 + d * local_u ** 3)

            return raw_eval, raw_intervals, display_intervals, ""

        # Fit a single Hermite-style spline on the full domain and plot it.
        try:
            hermite_fit_and_plot(xs, ys, color='b')
        except Exception:
            pass
        # clear legacy labels
        try:
            self._safe_set_label(self.function_label_raw, "")
            self._safe_set_label(self.function_label_display, "")
        except Exception:
            pass

    # Removed get_spline_evaluator to expose only a sampling API. The
    # sample_spline_display method below constructs the same Hermite-style
    # coefficients internally and returns sampled Y values in display units.

    def sample_spline_display(self, dx: float):
        """Sample the current plotted spline across the display-domain X range
        [xmin, xmax] at increments of dx (display units). Returns a numpy array
        of Y values (display units) sampled at x = xmin, xmin+dx, ..., <= xmax.

        This method builds the Hermite-style coefficients internally (same
        algorithm used when plotting) and evaluates the spline at each sample
        point. If fewer than two effective points exist, it returns a constant
        array equal to the mapped start endpoint.
        """
        try:
            dxv = float(dx)
        except Exception:
            return np.array([])
        if dxv <= 0:
            return np.array([])
        xmin = float(getattr(self, 'xmin', 0.0))
        xmax = float(getattr(self, 'xmax', 1.0))
        if xmax < xmin:
            return np.array([])

        # assemble raw pts including endpoints
        pts = list(zip(self.xPoints, self.yPoints))
        start_y = float(getattr(self, 'start_y', 0.0))
        end_y = float(getattr(self, 'end_y', 0.0))
        pts.append((0.0, start_y))
        pts.append((1.0, end_y))

        # deduplicate
        dedup = {}
        for x, y in pts:
            key = round(float(x), 12)
            if key in dedup and abs(dedup[key] - float(y)) > 1e-8:
                # conflict: return constant array of mapped start
                xs = np.arange(xmin, xmax + dxv * 0.5, dxv)
                return np.full(xs.shape, float(self._map_y(start_y)))
            dedup[key] = float(y)

        xs_raw = np.array(sorted(dedup.keys()))
        ys_raw = np.array([dedup[x] for x in xs_raw])

        # generate sample Xs in display domain
        xs = np.arange(xmin, xmax + dxv * 0.5, dxv)
        if xs.size == 0:
            return np.array([])

        if xs_raw.size < 2:
            # not enough points to build spline: return constant mapped start
            return np.full(xs.shape, float(self._map_y(start_y)))

        # compute Hermite tangents and per-interval coefficients
        order = np.argsort(xs_raw)
        x = np.asarray(xs_raw)[order]
        y = np.asarray(ys_raw)[order]
        n = x.size
        h = np.diff(x)
        # protect against zero-length intervals
        delta = np.zeros_like(h)
        try:
            delta = np.diff(y) / h
        except Exception:
            # fall back to zeros
            delta = np.zeros_like(h)

        m = np.zeros(n, dtype=float)
        if n == 2:
            m[0] = m[1] = delta[0]
        else:
            m[0] = delta[0]
            m[-1] = delta[-1]
            for i in range(1, n - 1):
                if delta[i - 1] == 0.0 or delta[i] == 0.0 or (delta[i - 1] < 0) != (delta[i] < 0):
                    m[i] = 0.0
                else:
                    denom = (h[i - 1] + h[i]) if (h[i - 1] + h[i]) != 0 else 1.0
                    m[i] = (h[i] * delta[i - 1] + h[i - 1] * delta[i]) / denom

        raw_intervals = []
        for i in range(n - 1):
            x0 = float(x[i])
            h_i = float(h[i])
            y0 = float(y[i])
            y1 = float(y[i + 1])
            m0 = float(m[i])
            m1 = float(m[i + 1])
            a = y0
            b = m0 * h_i
            c = -3 * y0 + 3 * y1 - 2 * m0 * h_i - m1 * h_i
            d = 2 * y0 - 2 * y1 + m0 * h_i + m1 * h_i
            raw_intervals.append([x0, h_i, a, b, c, d])

        # raw evaluator
        def raw_eval(u_query):
            uq = float(u_query)
            if uq <= x[0]:
                return float(y[0])
            if uq >= x[-1]:
                return float(y[-1])
            idx = np.searchsorted(x, uq) - 1
            if idx < 0:
                idx = 0
            if idx >= len(raw_intervals):
                idx = len(raw_intervals) - 1
            x0_i, h_i, a, b, c, d = raw_intervals[idx]
            local_u = (uq - x0_i) / h_i if h_i != 0 else 0.0
            local_u = np.clip(local_u, 0.0, 1.0)
            return float(a + b * local_u + c * local_u ** 2 + d * local_u ** 3)

        ys = np.empty(xs.shape, dtype=float)
        for i, xv in enumerate(xs):
            try:
                raw_u = self._unmap_x(float(xv))
                raw_y = raw_eval(raw_u)
                ys[i] = float(self._map_y(raw_y))
            except Exception:
                ys[i] = float(self._map_y(start_y))

        return ys

    def plotSineFunction(self):
        # Generate and plot the curve (same behavior as clicking)
        self.generate_and_plot_curve()

    def set_min_width(self, width: int):
        """Set a minimum width (pixels) for this widget to avoid squishing."""
        try:
            w = int(width)
        except Exception:
            return
        if w <= 0:
            return
        try:
            self.setMinimumWidth(w)
            self._min_width = w
        except Exception:
            pass

    def get_min_width(self) -> int:
        """Return the configured minimum width in pixels (or 0)."""
        return int(getattr(self, '_min_width', 0) or 0)

    def reset_bounds(self):
        """Reset mapping bounds to defaults and update the view.

        Sets xmin=0, xmax=1, ymin=0, ymax=1 and updates spins and view.
        """
        # Safely set mapping spins to defaults without repeating try/except blocks
        self._safe_block(self.xmin_spin, True)
        self._safe_block(self.xmax_spin, True)
        self._safe_block(self.ymin_spin, True)
        self._safe_block(self.ymax_spin, True)
        self._safe_set_spin_value(self.xmin_spin, 0.0)
        self._safe_set_spin_value(self.xmax_spin, 1.0)
        self._safe_set_spin_value(self.ymin_spin, 0.0)
        self._safe_set_spin_value(self.ymax_spin, 1.0)
        self._safe_block(self.xmin_spin, False)
        self._safe_block(self.xmax_spin, False)
        self._safe_block(self.ymin_spin, False)
        self._safe_block(self.ymax_spin, False)

        # Update internal mapping attributes and view ranges
        try:
            self.xmin = 0.0; self.xmax = 1.0; self.ymin = 0.0; self.ymax = 1.0
            try:
                self.plot_widget.setXRange(self.xmin, self.xmax)
                self.plot_widget.setYRange(self.ymin, self.ymax)
            except Exception:
                pass
        except Exception:
            pass

        # Ensure endpoint spinboxes show mapped values
        # Ensure endpoint spinboxes show mapped values
        self._safe_block(self.start_y_spin, True)
        self._safe_block(self.end_y_spin, True)
        self._safe_set_spin_range(self.start_y_spin, self.ymin, self.ymax)
        self._safe_set_spin_range(self.end_y_spin, self.ymin, self.ymax)
        self._safe_set_spin_value(self.start_y_spin, self._map_y(getattr(self, 'start_y', 0.0)))
        self._safe_set_spin_value(self.end_y_spin, self._map_y(getattr(self, 'end_y', 0.0)))
        self._safe_block(self.start_y_spin, False)
        self._safe_block(self.end_y_spin, False)

        # Update markers and curve to reflect reset bounds
        self._update_markers_mapped()
        self.generate_and_plot_curve()

    def reset_view_and_clear(self):
        """Clear points and reset the view bounds (connected to the header button)."""
        try:
            self.clearPlot()
        except Exception:
            pass
        try:
            # Reset configured start/end Y endpoints to their saved defaults and
            # update the spinboxes and plot. This preserves mapping bounds.
            # Desired display-default for endpoints is 0.0 (display units)
            desired_display = 0.0

            # Compute raw defaults corresponding to display 0.0 using current mapping
            raw_for_display0 = self._unmap_y(desired_display)
            # clamp to [0,1]
            raw_for_display0 = max(0.0, min(1.0, float(raw_for_display0)))

            # Update stored defaults and current endpoint raw values
            self._default_start_y = raw_for_display0
            self._default_end_y = raw_for_display0
            self.start_y = raw_for_display0
            self.end_y = raw_for_display0

            # Safely set the spinboxes to show 0.0 in display units even if their
            # current allowed range would not include 0. We temporarily expand the
            # spin range to include 0, set the value, then restore the original range.
            try:
                # remember original ranges
                orig_start_range = (self.start_y_spin.minimum(), self.start_y_spin.maximum())
                orig_end_range = (self.end_y_spin.minimum(), self.end_y_spin.maximum())
                # set ranges to include desired_display
                mn = min(orig_start_range[0], desired_display)
                mx = max(orig_start_range[1], desired_display)
                self._safe_set_spin_range(self.start_y_spin, mn, mx)
                mn2 = min(orig_end_range[0], desired_display)
                mx2 = max(orig_end_range[1], desired_display)
                self._safe_set_spin_range(self.end_y_spin, mn2, mx2)

                self._safe_block(self.start_y_spin, True)
                self._safe_block(self.end_y_spin, True)
                self._safe_set_spin_value(self.start_y_spin, desired_display)
                self._safe_set_spin_value(self.end_y_spin, desired_display)
                self._safe_block(self.start_y_spin, False)
                self._safe_block(self.end_y_spin, False)

                # restore original ranges
                self._safe_set_spin_range(self.start_y_spin, orig_start_range[0], orig_start_range[1])
                self._safe_set_spin_range(self.end_y_spin, orig_end_range[0], orig_end_range[1])
            except Exception:
                # fallback: set mapped values from raw defaults
                try:
                    self._safe_set_spin_value(self.start_y_spin, self._map_y(self.start_y))
                    self._safe_set_spin_value(self.end_y_spin, self._map_y(self.end_y))
                except Exception:
                    pass

            # Update endpoint markers and regenerate the curve (which will include endpoints)
            try:
                self._update_markers_mapped()
            except Exception:
                pass
            try:
                self.generate_and_plot_curve()
            except Exception:
                pass
        except Exception:
            pass

    # Polynomial/piecewise accessors removed — use get_spline_function_display or
    # sample_spline_display for programmatic evaluation of the plotted curve.

    

    # --- Axis units accessors -------------------------------------------------
    def set_x_units(self, units: str):
        """Set the X-axis units string shown on the bottom axis label.

        units: any object convertible to str (use empty string to clear).
        """
        try:
            u = "" if units is None else str(units)
        except Exception:
            u = ""
        self.x_units = u
        try:
            lbl = getattr(self, '_x_label_text', 'X-Axis')
            self.plot_widget.setLabel('bottom', lbl, units=u)
        except Exception:
            pass

    def get_x_units(self) -> str:
        """Return the current X-axis units string (may be empty)."""
        return getattr(self, 'x_units', '')

    def set_y_units(self, units: str):
        """Set the Y-axis units string shown on the left axis label."""
        try:
            u = "" if units is None else str(units)
        except Exception:
            u = ""
        self.y_units = u
        try:
            lbl = getattr(self, '_y_label_text', 'Y-Axis')
            self.plot_widget.setLabel('left', lbl, units=u)
        except Exception:
            pass

    def get_y_units(self) -> str:
        """Return the current Y-axis units string (may be empty)."""
        return getattr(self, 'y_units', '')

    def set_graph_title(self, title: str):
        """Set the plot title shown above the graph.

        Accepts any object convertible to string. Stores the title in
        self._graph_title for later retrieval.
        """
        try:
            t = "" if title is None else str(title)
        except Exception:
            t = ""
        try:
            self.plot_widget.setTitle(t)
        except Exception:
            pass
        try:
            self._graph_title = t
        except Exception:
            pass

    def get_graph_title(self) -> str:
        """Return the last set graph title (may be empty string)."""
        return getattr(self, '_graph_title', '')
    
    def get_current_points(self):
        """Return the current list of points as a list of (x_raw, y_raw) tuples."""
        #Get the start and end points as well, since they are part of the curve definition
        start_point = (0.0, self.start_y)
        end_point = (1.0, self.end_y)
        return [start_point] + list(zip(self.xPoints, self.yPoints)) + [end_point]

    def set_current_points(self, points):
        """Set the current list of points from a list of (x_raw, y_raw) tuples.

        This replaces the existing points with the provided list, updates the
        marker positions, and regenerates the curve. Points with x_raw outside
        [0,1] are ignored.
        """
        if not isinstance(points, (list, tuple)):
            return
        if len(points) < 2:
            return
        #Set the start and end points from the provided list if they exist
        self.start_y = float(points[0][1]) 
        self.end_y = float(points[-1][1])
        #Update the endpoint spinboxes to reflect the new start and end Y values
        self._safe_block(self.start_y_spin, True)
        self._safe_block(self.end_y_spin, True)
        self._safe_set_spin_value(self.start_y_spin, self._map_y(self.start_y))
        self._safe_set_spin_value(self.end_y_spin, self._map_y(self.end_y))
        self._safe_block(self.start_y_spin, False)
        self._safe_block(self.end_y_spin, False)

        #remove the start and end points from the list of points to be plotted as markers
        points = points[1:-1]
        new_xs = []
        new_ys = []
        for pt in points:
            try:
                x_raw = float(pt[0])
                y_raw = float(pt[1])
                if 0.0 <= x_raw <= 1.0:
                    new_xs.append(x_raw)
                    new_ys.append(y_raw)
            except Exception:
                continue
        self.xPoints = new_xs
        self.yPoints = new_ys
        self._update_markers_mapped()
        self.generate_and_plot_curve()




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show the main window
    window = InputGraph()
    window.setGeometry(100, 100, 800, 600) # x, y, width, height
    window.setWindowTitle("Input Graph")
    window.show()
    sys.exit(app.exec())