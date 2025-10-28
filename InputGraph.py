from PyQt6 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np
import sys

# Per-instance point storage (previously module-level globals) — removed globals below and
# use self.xPoints / self.yPoints so multiple InputGraph instances operate independently.

class InputGraph(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create layout for this widget
        layout = QtWidgets.QVBoxLayout(self)
        # --- Plot Setup ---
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'Y-Axis', units='units')
        self.plot_widget.setLabel('bottom', 'X-Axis', units='units')
        self.plot_widget.setTitle("Input Graph")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.hideButtons()
        self.plot_widget.setXRange(0,1)
        self.plot_widget.setYRange(0,1)
        # -- header with clear button in top-right corner ---
        header = QtWidgets.QHBoxLayout()
        header.addStretch()
        # use a larger reset/refresh symbol for clarity
        self.clear_button = QtWidgets.QPushButton("↺")
        # slightly larger circular red button so the symbol appears bigger
        self.clear_button.setFixedSize(34, 34)
        self.clear_button.setStyleSheet("background-color: #d9534f; color: white; border: none; border-radius: 17px; font-size: 16px;")
        # brief tooltip for clarity
        self.clear_button.setToolTip("Reset endpoints and clear points")
        # The clear button resets the view and clears points
        self.clear_button.clicked.connect(self.reset_view_and_clear)
        header.addWidget(self.clear_button)
        layout.addLayout(header)
        # Controls: endpoint Y values and degree (wrapped in a container so we can hide/show)
        controls_hbox = QtWidgets.QHBoxLayout()

        # Degree control
        self.degree_label = QtWidgets.QLabel("Degree:")
        self.degree_spin = QtWidgets.QSpinBox()
        self.degree_spin.setRange(1, 50)
        self.degree_spin.setValue(3)
        self.degree_spin.valueChanged.connect(self.onDegreeChanged)
        controls_hbox.addWidget(self.degree_label)
        controls_hbox.addWidget(self.degree_spin)

        # Start and End Y controls (float) constrained to [0,1]
        self.start_y_label = QtWidgets.QLabel("Start Y:")
        self.start_y_spin = QtWidgets.QDoubleSpinBox()
        self.start_y_spin.setRange(0.0, 1.0)
        self.start_y_spin.setSingleStep(0.01)
        self.start_y_spin.setValue(0.0)
        self.start_y_spin.valueChanged.connect(self.onEndpointChanged)
        # Put start/end Y controls into their own container so they can be hidden separately
        self.endpoints_container = QtWidgets.QWidget()
        endpoints_layout = QtWidgets.QHBoxLayout()
        endpoints_layout.setContentsMargins(0, 0, 0, 0)
        endpoints_layout.addWidget(self.start_y_label)
        endpoints_layout.addWidget(self.start_y_spin)

        self.end_y_label = QtWidgets.QLabel("End Y:")
        self.end_y_spin = QtWidgets.QDoubleSpinBox()
        self.end_y_spin.setRange(0.0, 1.0)
        self.end_y_spin.setSingleStep(0.01)
        self.end_y_spin.setValue(0.0)
        self.end_y_spin.valueChanged.connect(self.onEndpointChanged)
        endpoints_layout.addWidget(self.end_y_label)
        endpoints_layout.addWidget(self.end_y_spin)

        self.endpoints_container.setLayout(endpoints_layout)
        # remember natural height
        if hasattr(self.endpoints_container, 'sizeHint'):
            self._endpoints_prev_height = self.endpoints_container.sizeHint().height()
        else:
            self._endpoints_prev_height = None

        # Y mapping controls (output scaling/shifting)
        self.ymin_label = QtWidgets.QLabel("Y min:")
        self.ymin_spin = QtWidgets.QDoubleSpinBox()
        self.ymin_spin.setRange(-10000.0, 10000.0)
        self.ymin_spin.setSingleStep(0.1)
        self.ymin_spin.setValue(0.0)
        self.ymin_spin.valueChanged.connect(self.onMappingChanged)
        controls_hbox.addWidget(self.ymin_label)
        controls_hbox.addWidget(self.ymin_spin)

        self.ymax_label = QtWidgets.QLabel("Y max:")
        self.ymax_spin = QtWidgets.QDoubleSpinBox()
        self.ymax_spin.setRange(-10000.0, 10000.0)
        self.ymax_spin.setSingleStep(0.1)
        self.ymax_spin.setValue(1.0)
        self.ymax_spin.valueChanged.connect(self.onMappingChanged)
        controls_hbox.addWidget(self.ymax_label)
        controls_hbox.addWidget(self.ymax_spin)

        # X mapping controls (output scaling). Constrained to [0,10]
        self.xmin_label = QtWidgets.QLabel("X min:")
        self.xmin_spin = QtWidgets.QDoubleSpinBox()
        self.xmin_spin.setRange(0.0, 10.0)
        self.xmin_spin.setSingleStep(0.1)
        self.xmin_spin.setValue(0.0)
        self.xmin_spin.valueChanged.connect(self.onMappingChanged)
        controls_hbox.addWidget(self.xmin_label)
        controls_hbox.addWidget(self.xmin_spin)

        self.xmax_label = QtWidgets.QLabel("X max:")
        self.xmax_spin = QtWidgets.QDoubleSpinBox()
        self.xmax_spin.setRange(0.0, 10.0)
        self.xmax_spin.setSingleStep(0.1)
        self.xmax_spin.setValue(1.0)
        self.xmax_spin.valueChanged.connect(self.onMappingChanged)
        controls_hbox.addWidget(self.xmax_label)
        controls_hbox.addWidget(self.xmax_spin)

        # Wrap controls in a container widget so they can be hidden/shown together
        controls_vbox = QtWidgets.QVBoxLayout()
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
        # default endpoints (raw 0..1) used by reset; initialize to current values
        try:
            self._default_start_y = float(self.start_y)
            self._default_end_y = float(self.end_y)
        except Exception:
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
        bottom.addStretch()
        bottom.addWidget(self.endpoints_container)
        bottom.addStretch()
        self.max_points_label = QtWidgets.QLabel("Max points:")
        self.max_points_spin = QtWidgets.QSpinBox()
        self.max_points_spin.setRange(2, 1000)
        self.max_points_spin.setValue(10)
        self.max_points_spin.valueChanged.connect(self.onMaxPointsChanged)
        bottom.addWidget(self.max_points_label)
        bottom.addWidget(self.max_points_spin)
        bottom.addStretch()
        layout.addLayout(bottom)

        # Initialize per-instance stored points (raw in [0,1])
        self.xPoints = []
        self.yPoints = []

        # Create a ScatterPlotItem for markers so we can update markers without clearing the whole plot
        self.marker_scatter = pg.ScatterPlotItem(pen=pg.mkPen(None), brush='r', size=8)
        self.plot_widget.addItem(self.marker_scatter)
        # Separate scatter for the configured endpoints (mapped & scaled) so they
        # are visible even when no user points exist.
        self.endpoint_scatter = pg.ScatterPlotItem(pen=pg.mkPen('w'), brush='g', size=10, symbol='s')
        self.plot_widget.addItem(self.endpoint_scatter)

        # Prevent squishing: enforce a reasonable minimum width for this widget
        try:
            self._min_width = 220
            self.setMinimumWidth(self._min_width)
        except Exception:
            self._min_width = None
        # Track the plotted curve so we can remove it between generations
        self.curve_plot = None
        # Connect mouse click event
        self.plot_widget.scene().sigMouseClicked.connect(self.onClick)

    def onClick(self, event):
        # Only respond to left-button clicks (ignore other mouse buttons)
        try:
            if event.button() != QtCore.Qt.MouseButton.LeftButton:
                return
        except Exception:
            # Some event sources may not have button(); continue mapping position
            pass

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
            # Remove the clicked marker
            self.xPoints.pop(remove_index)
            self.yPoints.pop(remove_index)
            # Update scatter and regenerate curve (mapped)
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
            # drop oldest
            self.xPoints.pop(0)
            self.yPoints.pop(0)

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
        self.marker_scatter, self.endpoint_scatter = self._create_marker_scatter()
        if self.endpoint_scatter is not None and hasattr(self.endpoints_container, 'isVisible') and not self.endpoints_container.isVisible():
            self.endpoint_scatter.hide()
        # clear remembered curve
        self.curve_plot = None
        # clear stored polynomial and label
        self._poly = None
        self._poly_expr = ""
        # update labels safely
        self._safe_set_label(self.function_label_raw, "raw f(u) = ")
        self._poly_display = None
        self._poly_display_expr = ""
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

    def onDegreeChanged(self, val):
        """Called when the degree spinbox changes."""
        try:
            self.degree = int(val)
        except Exception:
            self.degree = None
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
        try:
            raw = float(value)
        except Exception:
            return
        self.end_y = raw
        # Safely update displayed spin
        self._safe_set_spin_value(self.end_y_spin, self._map_y(raw))

    def set_degree(self, value: int):
        """Set polynomial degree programmatically."""
        try:
            self.degree_spin.setValue(int(value))
        except Exception:
            try:
                self.degree = int(value)
            except Exception:
                pass

    def set_max_points(self, value: int):
        """Programmatically set the maximum stored points."""
        try:
            self.max_points_spin.setValue(int(value))
        except Exception:
            self.max_points = int(value)

    def set_default_endpoints(self, start_raw: float, end_raw: float, apply_now: bool = False):
        """Set default start/end Y endpoints (raw values in [0,1]).

        If apply_now is True, the widget will update the current endpoints
        to the provided defaults immediately (and update the spinboxes/plot).
        Otherwise the defaults are stored and used the next time the reset
        button is pressed.
        """
        try:
            s = float(start_raw)
        except Exception:
            return
        try:
            e = float(end_raw)
        except Exception:
            return
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

    def _poly_to_string(self, coeffs) -> str:
        """Return a compact human-readable polynomial string from coefficient array.

        coeffs: sequence from highest-degree to constant term.
        """
        try:
            coeffs = [float(c) for c in coeffs]
        except Exception:
            return ""
        terms = []
        deg = len(coeffs) - 1
        for i, c in enumerate(coeffs):
            power = deg - i
            if abs(c) < 1e-12:
                continue
            coeff_str = f"{c:.6g}"
            if power == 0:
                terms.append(f"{coeff_str}")
            elif power == 1:
                terms.append(f"{coeff_str}*x")
            else:
                terms.append(f"{coeff_str}*x**{power}")
        if not terms:
            return "0"
        expr = " + ".join(terms)
        expr = expr.replace("+ -", "- ")
        return expr

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
        """Create marker and endpoint scatter items and add to the plot widget.

        Returns (marker_scatter, endpoint_scatter).
        """
        ms = pg.ScatterPlotItem(pen=pg.mkPen(None), brush='r', size=8)
        es = None
        try:
            es = pg.ScatterPlotItem(pen=pg.mkPen('w'), brush='g', size=10, symbol='s')
        except Exception:
            try:
                es = pg.ScatterPlotItem(pen=pg.mkPen('w'), brush='g', size=10)
            except Exception:
                es = None
        try:
            self.plot_widget.addItem(ms)
            if es is not None:
                self.plot_widget.addItem(es)
        except Exception:
            pass
        return ms, es

    def _update_markers_mapped(self):
        """Update marker scatter using mapped coordinates."""
        mapped_x = [self._map_x(x) for x in self.xPoints]
        mapped_y = [self._map_y(y) for y in self.yPoints]
        self.marker_scatter.setData(x=mapped_x, y=mapped_y)
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
        try:
            self.controls_container.show()
            # restore previous height if available, otherwise use the sizeHint
            try:
                if getattr(self, '_controls_prev_height', None):
                    h = self._controls_prev_height
                else:
                    h = self.controls_container.sizeHint().height()
                # guard against zero/None
                if h and h > 0:
                    self.controls_container.setFixedHeight(h)
                else:
                    try:
                        self.controls_container.setFixedHeight(self.controls_container.sizeHint().height())
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def hide_endpoints(self):
        """Hide the start/end Y controls container and set its height to zero."""
        try:
            # Do not adjust the container height when hiding — simply hide it so the
            # layout can manage spacing. This preserves the natural height and avoids
            # forcing the layout to collapse.
            try:
                self.endpoints_container.hide()
            except Exception:
                pass
            try:
                self.endpoint_scatter.hide()
            except Exception:
                pass
        except Exception:
            pass

    def show_endpoints(self):
        """Show the start/end Y controls container and restore its height."""
        try:
            # Simply show the container without forcing a fixed height so layout
            # will naturally allocate its space.
            try:
                self.endpoints_container.show()
            except Exception:
                pass
            try:
                self.endpoint_scatter.show()
            except Exception:
                pass
        except Exception:
            pass

    def generate_and_plot_curve(self):
        """Fit a polynomial through the stored points plus endpoints and plot it.
        Removes any previously plotted curve before drawing the new one.
        """
        # Build point set: include clicked points and use configured endpoints
        pts = list(zip(self.xPoints, self.yPoints))
        # Use configured start/end values (fallback to 0.0)
        start_y = float(getattr(self, 'start_y', float(getattr(self, 'start_y_spin', 0.0).value() if hasattr(self, 'start_y_spin') else 0.0)))
        end_y = float(getattr(self, 'end_y', float(getattr(self, 'end_y_spin', 0.0).value() if hasattr(self, 'end_y_spin') else 0.0)))
        pts.append((0.0, start_y))
        pts.append((1.0, end_y))

        # If no points, remove existing curve and return
        if len(pts) == 0:
            if self.curve_plot is not None:
                try:
                    self.plot_widget.removeItem(self.curve_plot)
                except Exception:
                    pass
                self.curve_plot = None
            return

        # Deduplicate by x (round to avoid float tiny differences)
        dedup = {}
        for x, y in pts:
            key = round(float(x), 12)
            if key in dedup and abs(dedup[key] - float(y)) > 1e-8:
                return
            dedup[key] = float(y)

        xs = np.array(sorted(dedup.keys()))
        ys = np.array([dedup[x] for x in xs])

        if xs.size < 2:
            # not enough distinct x values
            if self.curve_plot is not None:
                try:
                    self.plot_widget.removeItem(self.curve_plot)
                except Exception:
                    pass
                self.curve_plot = None
            return

        # Use requested degree but cap at (n-1) where n is number of distinct x's
        try:
            requested_deg = int(self.degree_spin.value()) if hasattr(self, 'degree_spin') else (xs.size - 1)
        except Exception:
            requested_deg = xs.size - 1

        max_deg = max(1, xs.size - 1)
        if requested_deg > max_deg:
            # cap the degree to the maximum supported by the data
            pass
        deg = min(requested_deg, max_deg)

        coeffs = np.polyfit(xs, ys, deg)
        poly = np.poly1d(coeffs)

        # store polynomial for accessor
        try:
            self._poly = poly
        except Exception:
            self._poly = None

        # Build a readable expression and display it in the controls label
        try:
            expr = self._poly_to_string(coeffs)
            self._poly_expr = expr
            # update raw-domain label (u in [0,1])
            try:
                self.function_label_raw.setText(f"raw f(u) = {expr}")
            except Exception:
                pass
        except Exception:
            self._poly_expr = ""
        # Also compute a display-domain polynomial (scaled/shifted to plot coordinates)
        try:
            xmin = float(getattr(self, 'xmin', 0.0))
            xmax = float(getattr(self, 'xmax', 1.0))
            ymin = float(getattr(self, 'ymin', 0.0))
            ymax = float(getattr(self, 'ymax', 1.0))
            scale_x = (xmax - xmin) if (xmax - xmin) != 0 else 1.0
            scale_y = (ymax - ymin) if (ymax - ymin) != 0 else 1.0
            # sample many points in display X range, compute mapped y and fit same-degree polynomial
            sample_x = np.linspace(xmin, xmax, max(301, deg * 50))
            # convert display x to raw u in [0,1]
            u = (sample_x - xmin) / scale_x
            y_display_vals = ymin + scale_y * poly(u)
            disp_coeffs = np.polyfit(sample_x, y_display_vals, deg)
            disp_poly = np.poly1d(disp_coeffs)
            self._poly_display = disp_poly
            self._poly_display_expr = self._poly_to_string(disp_coeffs)
            try:
                # Update the display-domain label to show the scaled/shifted function
                self.function_label_display.setText(f"display f(x) = {self._poly_display_expr}")
            except Exception:
                pass
        except Exception:
            self._poly_display = None
            self._poly_display_expr = ""
        # Polynomial computed (coeffs available in variable 'coeffs')

        # Prepare curve in raw coordinates (0..1), then map to display coordinates
        x_plot = np.linspace(0.0, 1.0, 500)
        y_plot = poly(x_plot)
        # Clip raw y to [0,1] so polynomial stays within expected input domain
        y_plot = np.clip(y_plot, 0.0, 1.0)

        # Map curve into display coordinates for plotting
        mapped_x_plot = [self._map_x(xx) for xx in x_plot]
        mapped_y_plot = [self._map_y(yy) for yy in y_plot]

        # Remove previous curve if present
        if self.curve_plot is not None:
            try:
                self.plot_widget.removeItem(self.curve_plot)
            except Exception:
                pass
            self.curve_plot = None

        # Plot and remember the plotted curve item (mapped coordinates)
        self.curve_plot = self.plot_widget.plot(mapped_x_plot, mapped_y_plot, pen=pg.mkPen('b', width=2))

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
            default_start = float(getattr(self, '_default_start_y', 0.0))
            default_end = float(getattr(self, '_default_end_y', 0.0))
            self.start_y = default_start
            self.end_y = default_end
            # Use helpers to update endpoint spinboxes safely
            self._safe_block(self.start_y_spin, True)
            self._safe_block(self.end_y_spin, True)
            self._safe_set_spin_value(self.start_y_spin, self._map_y(self.start_y))
            self._safe_set_spin_value(self.end_y_spin, self._map_y(self.end_y))
            self._safe_block(self.start_y_spin, False)
            self._safe_block(self.end_y_spin, False)

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

    # Accessors for polynomial
    def get_polynomial(self):
        """Return the last computed numpy.poly1d polynomial (in raw [0..1] domain) or None."""
        return getattr(self, '_poly', None)

    def get_polynomial_string(self) -> str:
        """Return the last computed polynomial expression string (human-readable) or empty string."""
        return getattr(self, '_poly_expr', "")

    def get_polynomial_display(self):
        """Return the last computed numpy.poly1d polynomial in display coordinates (x in [xmin,xmax]) or None."""
        return getattr(self, '_poly_display', None)

    def get_polynomial_display_string(self) -> str:
        """Return the last computed display-domain polynomial expression string or empty string."""
        return getattr(self, '_poly_display_expr', "")

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



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show the main window
    window = InputGraph()
    window.setGeometry(100, 100, 800, 600) # x, y, width, height
    window.setWindowTitle("Input Graph")
    window.show()
    sys.exit(app.exec())