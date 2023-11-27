import textwrap
from typing import TYPE_CHECKING

import numpy as np
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton, QFileDialog
from magicgui import magicgui
from napari_matplotlib.base import NapariMPLWidget
import psf_extractor as psfe
from qtpy.QtWidgets import QWidget
from superqt import QRangeSlider

from napari_psf_extractor.extractor import extract_psf
from napari_psf_extractor.features import Features
from napari_psf_extractor.utils import normalize

# Hide napari imports from type support and autocompletion
# https://napari.org/stable/guides/magicgui.html?highlight=type_checking
if TYPE_CHECKING:
    pass

from napari.layers.image.image import Image


def create_range_slider_widget(min_value=0, max_value=100):
    range_slider = QRangeSlider(Qt.Orientation.Horizontal)

    range_slider.setRange(min_value, max_value)
    range_slider.setValue((min_value, max_value))
    range_label = QLabel(f"Range: [{min_value}, {max_value}]")

    return range_slider, range_label


class MainWidget(QWidget):
    """
    Main widget for the PSF Extractor plugin.
    """

    def __init__(self, napari_viewer, parent=None):

        # ------------------
        # MagicGUI functions
        # ------------------

        @magicgui(
            call_button="Find features",
            psx={"tooltip": "Pixel size in x-direction [nm/px]"},
            psy={"tooltip": "Pixel size in y-direction [nm/px]"},
            psz={"tooltip": "Pixel size in z-direction [nm/px]"},
            na={"tooltip": "Numerical aperture of the objective"},
            lambda_emission={"tooltip": "Emission wavelength [nm]"}
        )
        def param_setter(
                image_layer: Image,
                psx: float = 63.5,
                psy: float = 63.5,
                psz: float = 100,
                na: float = 0.85,
                lambda_emission: float = 520,
        ):
            if image_layer is None:
                print("Error: Please select an image stack.")
                return

            # Check if any of the input elements is equal to 0
            if psx == 0 or psy == 0 or psz == 0 or na == 0 or lambda_emission == 0:
                print("Error: All input elements must be non-zero.")
                return

            self._init_optical_settings(lambda_emission, na, psx, psy, psz, image_layer)

            self.stack = normalize(np.array(image_layer.data, dtype=np.float32))
            self.mip = np.max(self.stack, axis=0)

            self.state = 0
            self.refresh()

        # ---------------------
        # Widget initialization
        # ---------------------

        super().__init__(parent=parent)

        self.viewer = napari_viewer

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(param_setter.native)

        self.features = Features(self)

        self.state = 0
        self.stack = None
        self.mip = None
        self.range_slider_values = [0, 100]

        # Widgets
        self.range_slider, self.range_label = create_range_slider_widget(
            min_value=self.range_slider_values[0],
            max_value=self.range_slider_values[1]
        )
        self.range_slider.hide()
        self.range_label.hide()

        self.plot_widget = NapariMPLWidget(napari_viewer, parent=self)
        self.plot_widget.hide()

        self.save_button = QPushButton("Save PSF")
        self.save_button.hide()

        # Add hidden widgets to layout
        self.layout().addWidget(self.range_slider)
        self.layout().addWidget(self.range_label)
        self.layout().addWidget(self.save_button)

        # ---------------
        # Connect Signals
        # ---------------

        self.range_slider.valueChanged.connect(self.update_range_label)
        self.save_button.clicked.connect(self.save_psf)

        self.viewer.layers.events.inserted.connect(param_setter.reset_choices)
        self.viewer.layers.events.removed.connect(param_setter.reset_choices)

        # Create a QTimer to handle delayed updates
        self.features_timer = QTimer()
        self.features_timer.setSingleShot(True)
        self.features_timer.timeout.connect(self.features.update)

    def _init_optical_settings(self, lambda_emission, na, psx, psy, psz, image_layer):
        """
        Initialize optical settings.
        """
        self.psx = psx
        self.psy = psy
        self.psz = psz

        # Set expected feature diameters [nm]
        dx_nm = lambda_emission / na
        dy_nm = dx_nm
        dz_nm = 3 * dx_nm

        # Convert expected feature diameters [nm --> px]
        dx = dx_nm / psx
        dy = dy_nm / psy
        dz = dz_nm / psz

        # Round diameters up to nearest odd integer (as per `trackpy` instructions)
        self.dx, self.dy, self.dz = np.ceil([dx, dy, dz]).astype(int) // 2 * 2 + 1

        # Set PSF window
        self.wx = int(np.round(4 * dx_nm / psx))  # px
        self.wy = int(np.round(4 * dy_nm / psx))  # px
        self.wz = int(np.round(10 * dx_nm / psz))  # px

        # Output
        out = textwrap.dedent(f"""\
            Optical settings
            ----------------
            NA.............. {na:.2f}
            Wavelength...... {lambda_emission:.0f} nm
            Pixelsize x..... {psx:.1f} nm/px
            Pixelsize y..... {psy:.1f} nm/px
            Pixelsize z..... {psz:.1f} nm/px
            Diameter x...... {self.dx:.0f} px ({dx_nm:.1f} nm)
            Diameter y...... {self.dy:.0f} px ({dy_nm:.1f} nm)
            Diameter z...... {self.dz:.0f} px ({dz_nm:.1f} nm)
            PSF window x.... {self.wx:.0f} px ({self.wx * psx:.0f} nm)
            PSF window y.... {self.wy:.0f} px ({self.wy * psy:.0f} nm)
            PSF window z.... {self.wz:.0f} px ({self.wz * psz:.0f} nm)
            """)

        print(f"Image layer: {image_layer}", '\n')
        print(out)

    def refresh(self):
        """
        Refresh the widget and move to the next state.
        """
        if self.state == 0:
            self.range_slider.show()
            self.range_label.show()
            self.save_button.show()

            self.range_slider.setValue(
                (self.range_slider_values[0], self.range_slider_values[1])
            )

            # Move to next state
            self.state = 1

        elif self.state == 1:
            self.save_button.show()

            # Move to next state
            self.state = 2

    def update_range_label(self, mass_range):
        """
        Update the range label. This function is called when the range slider is moved.
        """
        self.range_label.setText(f"Mass Range: [{mass_range[0]}, {mass_range[1]}]")

        # Restart the timer
        if self.features_timer.isActive():
            self.features_timer.stop()

        # Timer used to prevent excessive and rapid updates (32 ms)
        self.features_timer.start(32)

    def viewer_has_layer(self, layer_name):
        """
        Check if a layer with the given name is already present in the viewer.
        """
        return any(layer.name == layer_name for layer in self.viewer.layers)

    def save_psf(self):
        """
        Save the extracted PSF to a file.
        """
        self.save_button.setEnabled(False)

        # Open a folder selection dialog
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly

        folder_path = QFileDialog.getExistingDirectory(
            None, "Select a folder to save the stack",
            options=options
        )

        # Check if user selected a folder
        if folder_path:
            folder_path = folder_path + "/"

            try:
                psf_sum = extract_psf(
                    min_mass=self.range_slider.value()[0],
                    max_mass=self.range_slider.value()[1],
                    stack=self.stack,
                    features=self.features.get_features(),
                    wx=self.wx, wy=self.wy, wz=self.wz
                )

                # Save PSF results to folder
                psfe.save_stack(
                    psf_sum, folder_path,
                    psx=self.psx, psy=self.psy, psz=self.psz, usf=5
                )
            except Exception as e:
                # TODO: find why this breaks matplotlib
                # show_error(f"Error: {e}")
                print(e)

        self.save_button.setEnabled(True)
