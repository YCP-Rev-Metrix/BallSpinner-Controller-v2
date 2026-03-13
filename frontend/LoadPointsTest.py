import sys

from PyQt6 import QtWidgets

from InputGraph import InputGraph


class LoadPointsTestWindow(QtWidgets.QWidget):
    """Window containing two InputGraphs and Store/Load buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load/Store InputGraph Points")

        # Layout: graphs on top, buttons on bottom
        self._graph_a = InputGraph()
        self._graph_b = InputGraph()

        graphs_layout = QtWidgets.QHBoxLayout()
        graphs_layout.addWidget(self._graph_a)
        graphs_layout.addWidget(self._graph_b)

        self._btn_store = QtWidgets.QPushButton("Store")
        self._btn_load = QtWidgets.QPushButton("Load")

        # Buttons are intentionally no-op.
        self._btn_store.clicked.connect(self.storeGraphAPoints)
        self._btn_load.clicked.connect(self.loadGraphBPoints)

        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self._btn_store)
        buttons_layout.addWidget(self._btn_load)
        buttons_layout.addStretch()

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(graphs_layout)
        main_layout.addLayout(buttons_layout)

        self.points = []  # This will hold the points stored from Graph A to be loaded into Graph B

    def storeGraphAPoints(self):
        """Store the current points from Graph A."""
        self.points = self._graph_a.get_current_points()
        print(f"Storing Graph A points: {self.points}")

    def loadGraphBPoints(self):
        """Load points into Graph B."""
        self._graph_b.set_current_points(self.points)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = LoadPointsTestWindow()
    win.resize(1200, 800)
    win.show()
    sys.exit(app.exec())
