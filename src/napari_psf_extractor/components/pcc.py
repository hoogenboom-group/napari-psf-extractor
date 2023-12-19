from napari.utils.notifications import show_error
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QLineEdit, QHBoxLayout, QCheckBox, QWidget, QVBoxLayout, QLabel, QPushButton

from napari_psf_extractor.extractor import extract_psf


class PCC(QWidget):
    changed = Signal()

    def __init__(self, widget):
        super().__init__()

        self.widget = widget
        self.pcc_min = QLineEdit("0.7")
        self.checkbox = QCheckBox("PCC")
        self.features_pcc_label = QLabel("Remaining features:")
        self.filter_button = QPushButton("Filter")

        self.update_checkbox()

        # Layout
        layout = QVBoxLayout()

        value_layout = QHBoxLayout()
        value_layout.addWidget(self.checkbox)
        value_layout.addWidget(self.pcc_min)
        value_layout.addStretch()
        layout.addLayout(value_layout)

        layout.addWidget(self.filter_button)
        layout.addWidget(self.features_pcc_label)

        self.setLayout(layout)

        # Signals
        self.checkbox.stateChanged.connect(self.update_checkbox)
        self.filter_button.clicked.connect(self.filter)

        self.pcc_min.textChanged.connect(self.emit_changed)

    def emit_changed(self):
        self.changed.emit()

    def update_checkbox(self):
        if not self.checkbox.isChecked():
            self.pcc_min.hide()
            self.features_pcc_label.hide()
            self.filter_button.hide()

        elif not self.pcc_min.isVisible():
            self.pcc_min.show()
            self.features_pcc_label.show()
            self.filter_button.show()

            self.pcc_min.setText("0.7")
            self.features_pcc_label.setText("Remaining features:")

        self.emit_changed()

    def value(self):
        """
        Get the current PCC value. If PCC filtering is not enabled, return None.
        """
        if self.checkbox.isChecked():
            try:
                return float(self.pcc_min.text())
            except ValueError:
                show_error("Error: PCC must be a number.")
                return None
        else:
            return None

    def set_features_label(self, features):
        """
        Set the features label to the number of features.
        """
        self.features_pcc_label.setText(f"Remaining features: {len(features)}")

    def filter(self):
        """
        Update the features label when the PCC value changes.
        """

        features = self.widget.features.get_features()

        if self.value() is None or features is None:
            return

        try:
            _, features = extract_psf(
                min_mass=self.widget.mass_slider.value()[0],
                max_mass=self.widget.mass_slider.value()[1],
                stack=self.widget.stack,
                features=features,
                wx=self.widget.wx, wy=self.widget.wy, wz=self.widget.wz,
                pcc_min=self.value()
            )

            self.set_features_label(features)
        except Exception as e:
            show_error(f"Error: {e}")
