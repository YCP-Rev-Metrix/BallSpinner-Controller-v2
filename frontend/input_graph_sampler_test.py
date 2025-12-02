from PyQt6 import QtWidgets
import pyqtgraph as pg
import numpy as np
import sys

from .InputGraph import InputGraph


class SamplerWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('InputGraph Sampler Test')

        # Use a horizontal layout so the two graphs appear side-by-side.
        layout = QtWidgets.QVBoxLayout(self)

        main_row = QtWidgets.QHBoxLayout()

        # Left: the interactive InputGraph
        self.input_graph = InputGraph()
        main_row.addWidget(self.input_graph, stretch=1)

        # Right: controls above and the output plot below
        right_col = QtWidgets.QVBoxLayout()
        controls = QtWidgets.QHBoxLayout()
        controls.addWidget(QtWidgets.QLabel('dx:'))
        self.dx_edit = QtWidgets.QLineEdit('0.01')
        self.dx_edit.setFixedWidth(80)
        controls.addWidget(self.dx_edit)
        self.sample_btn = QtWidgets.QPushButton('Sample & Plot')
        controls.addWidget(self.sample_btn)
        controls.addStretch()

        right_col.addLayout(controls)

        # Output pyqtgraph plot (on the right)
        self.out_plot = pg.PlotWidget()
        self.out_plot.setBackground('w')
        self.out_plot.getPlotItem().setLabel('left', 'Y (display)')
        self.out_plot.getPlotItem().setLabel('bottom', 'X (display)')
        right_col.addWidget(self.out_plot, stretch=1)

        main_row.addLayout(right_col, stretch=1)

        layout.addLayout(main_row)

        # Connect button
        self.sample_btn.clicked.connect(self.on_sample)

        # Add a few default points so the InputGraph isn't empty
        try:
            # simple hump
            self.input_graph.xPoints = [0.0, 0.25, 0.5, 0.75, 1.0]
            self.input_graph.yPoints = [0.0, 0.4, 0.9, 0.4, 0.0]
            self.input_graph._update_markers_mapped()
            self.input_graph.generate_and_plot_curve()
        except Exception:
            pass

    def on_sample(self):
        try:
            dx = float(self.dx_edit.text())
        except Exception:
            dx = 0.01

        # Get mapped domain to reconstruct sample X coordinates
        xmin = float(getattr(self.input_graph, 'xmin', 0.0))
        xmax = float(getattr(self.input_graph, 'xmax', 1.0))

        ys = self.input_graph.sample_spline_display(dx)
        # Build corresponding xs the same way the sampler does
        xs = np.arange(xmin, xmax + dx * 0.5, dx)

        # Guard length mismatch
        if ys.size != xs.size:
            # truncate or pad with endpoint value
            if ys.size == 0:
                xs = np.array([])
            elif ys.size < xs.size:
                xs = xs[: ys.size]
            else:
                ys = ys[: xs.size]

        # Plot sampled points
        try:
            self.out_plot.clear()
            if xs.size > 0:
                self.out_plot.plot(xs, ys, pen=None, symbol='o', symbolBrush='r', symbolSize=6)
        except Exception as e:
            #print('Plot error:', e)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = SamplerWindow()
    w.resize(1000, 700)
    w.show()
    sys.exit(app.exec())
