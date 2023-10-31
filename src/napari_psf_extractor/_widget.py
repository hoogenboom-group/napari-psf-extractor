import textwrap
from typing import TYPE_CHECKING

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QLabel
from magicgui import magicgui
from napari.utils.notifications import show_error
from qtpy.QtWidgets import QWidget
from superqt import QRangeSlider

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
                show_error("Error: Please select an image stack.")
                return

            # Check if any of the input elements is equal to 0
            if psx == 0 or psy == 0 or psz == 0 or na == 0 or lambda_emission == 0:
                show_error("Error: All input elements must be non-zero.")
                return

            self._init_optical_settings(lambda_emission, na, psx, psy, psz, image_layer)

            self.stack = normalize(np.array(image_layer.data, dtype=np.float32))
            self.mip = np.max(self.stack, axis=0)

            self.refresh()

        # ---------------------
        # Widget initialization
        # ---------------------

        super().__init__(parent=parent)

        self.viewer = napari_viewer

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(param_setter.native)

        self.state = 0

        # ---------------
        # Connect Signals
        # ---------------

        self.viewer.layers.events.inserted.connect(param_setter.reset_choices)
        self.viewer.layers.events.removed.connect(param_setter.reset_choices)

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
            # Move to next state
            self.state = 1
