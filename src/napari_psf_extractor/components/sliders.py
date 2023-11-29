from qtpy.QtWidgets import QLabel, QVBoxLayout, QWidget
from qtpy.QtCore import Qt, QTimer
from superqt import QRangeSlider


class RangeSlider(QWidget):
    """
    Range slider widget.
    """
    def __init__(self, min_value, max_value, callback):
        """
        Initialize the range slider widget.

        Parameters
        ----------
        min_value : int
            The minimum value of the range slider.
        max_value : int
            The maximum value of the range slider.
        callback : function
            The function to call when the range slider is moved.
        """
        super().__init__()

        self.slider = QRangeSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(min_value, max_value)
        self.slider.setValue((min_value, max_value))

        self.label = QLabel(f"Range: [{min_value}, {max_value}]")

        # QTimer to handle delayed updates
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(callback)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        self.setLayout(layout)

        # Signals
        self.slider.valueChanged.connect(self.update_range)

    def update_range(self):
        """
        Update the range label. This function is called when the range slider is moved.
        """
        mass_range = self.slider.value()

        self.label.setText(f"Mass Range: [{mass_range[0]}, {mass_range[1]}]")

        # Restart the timer
        if self.timer.isActive():
            self.timer.stop()

        # Timer used to prevent excessive and rapid updates (32 ms)
        self.timer.start(32)

    def reset(self):
        """
        Reset the range slider to its initial state.
        """
        self.slider.setValue((self.slider.minimum(), self.slider.maximum()))

    def value(self):
        return self.slider.value()
