from napari.utils.notifications import show_error
from qtpy.QtCore import Qt, QTimer
from qtpy.QtWidgets import QLabel, QLineEdit, QHBoxLayout, QVBoxLayout, QWidget
from superqt import QRangeSlider


class RangeSlider(QWidget):
    """
    Range slider widget.
    """

    def __init__(self, min_value, max_value, callback):
        """
        Initialize the range slider widget.
        The slider values are in units of 0.1.

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

        # Set the range slider values to be in units of 0.1
        max_value = max_value * 10

        self.slider = QRangeSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(min_value, max_value)
        self.slider.setValue((min_value, max_value))

        self.min_label = QLabel("Min:")
        self.max_label = QLabel("Max:")
        self.min_value_edit = QLineEdit(str(min_value))
        self.max_value_edit = QLineEdit(str(max_value))

        # Layout
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.min_label)
        input_layout.addWidget(self.min_value_edit)
        input_layout.addWidget(self.max_label)
        input_layout.addWidget(self.max_value_edit)

        layout = QVBoxLayout()
        layout.addLayout(input_layout)
        layout.addWidget(self.slider)
        self.setLayout(layout)

        # Signals
        self.slider.valueChanged.connect(self.update_range)
        self.min_value_edit.editingFinished.connect(self.input_change)
        self.max_value_edit.editingFinished.connect(self.input_change)

        # QTimer to handle delayed updates
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(callback)

    def update_range(self):
        """
        Update the range label. This function is called when the range slider is moved.
        """
        mass_range = self.slider.value()
        self.min_value_edit.setText(str(mass_range[0] / 10))
        self.max_value_edit.setText(str(mass_range[1] / 10))

        # Restart the timer
        if self.timer.isActive():
            self.timer.stop()

        # Timer used to prevent excessive and rapid updates (32 ms)
        self.timer.start(32)

    def input_change(self):
        """
        Update the slider values based on the text input fields.
        """
        try:
            min_value = float(self.min_value_edit.text()) * 10
            max_value = float(self.max_value_edit.text()) * 10
        except ValueError:
            show_error("Error: Invalid input.")
            return

        if min_value > max_value:
            show_error("Error: Min value must be less than or equal to max value.")
            return

        self.slider.setValue((min_value, max_value))

    def reset(self):
        """
        Reset the range slider to its initial state.
        """
        self.slider.setValue((self.slider.minimum(), self.slider.maximum()))

    def value(self):
        return self.slider.value()[0] / 10, self.slider.value()[1] / 10
