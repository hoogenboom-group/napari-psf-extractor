from typing import TYPE_CHECKING

import numpy as np
import psf_extractor as psfe
from magicgui import magicgui
from matplotlib import pyplot as plt
from napari.utils.notifications import show_error, show_info
from qtpy.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QHBoxLayout

from napari_psf_extractor.components.pcc import PCC
from napari_psf_extractor.components.sliders import RangeSlider
from napari_psf_extractor.components.statusbar import StatusMessage
from napari_psf_extractor.extractor import extract_psf
from napari_psf_extractor.features import Features
from napari_psf_extractor.plotting import plot_psf
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
            psx={"tooltip": "Pixel size in x-direction [nm/px]"},
            psy={"tooltip": "Pixel size in y-direction [nm/px]"},
            psz={"tooltip": "Pixel size in z-direction [nm/px]"},
            na={"tooltip": "Numerical aperture of the objective"},
            lambda_emission={"tooltip": "Emission wavelength [nm]"},
            auto_call=True
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

            # Disable buttons on parameters change
            self.disable_non_param_widgets()

            # Check if the image has changed
            if self.img_name != image_layer.name:
                self.stack = normalize(np.array(image_layer.data, dtype=np.float32))
                self.mip = np.max(self.stack, axis=0)

                self.img_name = image_layer.name

        # ---------------------
        # Widget initialization
        # ---------------------

        super().__init__(parent=parent)

        self.viewer = napari_viewer

        self.features = Features(self)
        self.status = StatusMessage(self.viewer)
        self.mass_slider = RangeSlider(
            min_value=0, max_value=100,
            callback=self.features.update,
            result_label=self.features.label
        )
        self.save_button = QPushButton("Save")
        self.extract_button = QPushButton("Extract")
        self.find_features_button = QPushButton("Find features")
        self.pcc = PCC(self)

        self.plot_fig = plt.figure()
        self.img_name = None
        self.stack = None
        self.mip = None
        self.psf_sum = None

        self.hide_all()

        # ---------------
        # Layout
        # ---------------

        self.setLayout(QVBoxLayout())

        self.layout().addWidget(param_setter.native)
        self.layout().addWidget(self.find_features_button)
        self.layout().addWidget(self.mass_slider)
        self.layout().addWidget(self.pcc)

        self.layout().addStretch(1)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.extract_button)
        buttons_layout.addWidget(self.save_button)
        self.layout().addLayout(buttons_layout)

        # ---------------
        # Connect Signals
        # ---------------

        self.save_button.clicked.connect(self.save_to_folder)
        self.extract_button.clicked.connect(self.extract)
        self.find_features_button.clicked.connect(self.find_features)

        self.pcc.changed.connect(lambda: self.save_button.setEnabled(False))

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

    def hide_all(self):
        """
        Hide all widgets.
        """
        self.mass_slider.hide()
        self.features.label.hide()
        self.pcc.hide()
        self.extract_button.hide()
        self.save_button.hide()

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
                # Save PSF results to folder
                psfe.save_stack(
                    self.psf_sum, folder_path,
                    psx=self.psx, psy=self.psy, psz=self.psz, usf=5
                )
            except Exception as e:
                show_error(f"Error: {e}")

        show_info("PSF stack saved successfully.")
        self.save_button.setEnabled(True)

    def extract(self):
        """
        Extract PSFs from the selected image stack.

        This function is called when the "Extract" button is clicked.
        """
        try:
            self.psf_sum, _ = extract_psf(
                min_mass=self.mass_slider.value()[0],
                max_mass=self.mass_slider.value()[1],
                stack=self.stack,
                features=self.features.get_features(),
                wx=self.wx, wy=self.wy, wz=self.wz,
                pcc_min=self.pcc.value()
            )

            # Plot extracted PSFs
            plot_psf(self.psf_sum, self.psx, self.psy, self.psz)

            self.save_button.setEnabled(True)
        except Exception as e:
            show_error(f"Error: {e}")

    def find_features(self):
        """
        Find features in the selected image stack.
        """
        self.mass_slider.reset()
        self.features.label.show()
        self.mass_slider.show()
        self.save_button.show()
        self.extract_button.show()
        self.pcc.show()

        # Enable all widgets, except for the save button
        self.pcc.setEnabled(True)
        self.mass_slider.setEnabled(True)
        self.extract_button.setEnabled(True)

    def disable_non_param_widgets(self):
        """
        Disable all widgets except for the parameter setter.

        This function is called when the parameters are changed
        and the features found become outdated.
        """
        self.pcc.setEnabled(False)
        self.mass_slider.setEnabled(False)
        self.extract_button.setEnabled(False)
        self.save_button.setEnabled(False)
