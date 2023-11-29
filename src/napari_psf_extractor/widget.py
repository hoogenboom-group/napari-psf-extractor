from typing import TYPE_CHECKING

import numpy as np
import psf_extractor as psfe
from magicgui import magicgui
from matplotlib import pyplot as plt
from napari.utils.notifications import show_error
from qtpy.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog

from napari_psf_extractor.components.sliders import RangeSlider
from napari_psf_extractor.components.statusbar import StatusMessage
from napari_psf_extractor.extractor import extract_psf
from napari_psf_extractor.features import Features
from napari_psf_extractor.utils import normalize

# Hide napari imports from type support and autocompletion
# https://napari.org/stable/guides/magicgui.html?highlight=type_checking
if TYPE_CHECKING:
    pass

from napari.layers.image.image import Image


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
                show_error("Error: Please select an image stack.")
                return

            # Check if any of the input elements is equal to 0
            if psx == 0 or psy == 0 or psz == 0 or na == 0 or lambda_emission == 0:
                show_error("Error: All input elements must be non-zero.")
                return

            self._init_optical_settings(lambda_emission, na, psx, psy, psz)

            self.stack = normalize(np.array(image_layer.data, dtype=np.float32))
            self.mip = np.max(self.stack, axis=0)

            self.reset()
            self.refresh()

        # ---------------------
        # Widget initialization
        # ---------------------

        super().__init__(parent=parent)

        self.viewer = napari_viewer

        self.features = Features(self)
        self.status = StatusMessage(self.viewer)
        self.mass_slider = RangeSlider(0, 100, callback=self.features.update)
        self.save_button = QPushButton("Save PSF")

        self.plot_fig = plt.figure()
        self.state = None
        self.stack = None
        self.mip = None

        self.reset()

        # ---------------
        # Layout
        # ---------------

        self.setLayout(QVBoxLayout())

        self.layout().addWidget(param_setter.native)
        self.layout().addWidget(self.mass_slider)
        self.layout().addWidget(self.features.label)
        self.layout().addStretch(1)
        self.layout().addWidget(self.save_button)

        # ---------------
        # Connect Signals
        # ---------------

        self.save_button.clicked.connect(self.save_to_folder)

        self.viewer.layers.events.inserted.connect(param_setter.reset_choices)
        self.viewer.layers.events.removed.connect(param_setter.reset_choices)

    def _init_optical_settings(self, lambda_emission, na, psx, psy, psz):
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
        self.wx = int(np.round(4 * dx_nm / psx))    # px
        self.wy = int(np.round(4 * dy_nm / psx))    # px
        self.wz = int(np.round(10 * dx_nm / psz))   # px

    def reset(self):
        self.state = 0

        self.mass_slider.hide()
        self.save_button.hide()
        self.features.label.hide()

    def refresh(self):
        """
        Refresh the widget and move to the next state.
        """
        if self.state == 0:
            self.mass_slider.reset()
            self.features.label.show()
            self.mass_slider.show()
            self.save_button.show()

            # Move to next state
            self.state = 1

        elif self.state == 1:
            self.save_button.show()

            # Move to next state
            self.state = 2

    def save_to_folder(self):
        """
        Save the extracted PSF to a folder.
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
                    min_mass=self.mass_slider.value()[0],
                    max_mass=self.mass_slider.value()[1],
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
                show_error(f"Error: {e}")

        self.save_button.setEnabled(True)
