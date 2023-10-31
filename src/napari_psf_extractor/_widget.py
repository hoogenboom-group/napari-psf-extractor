import textwrap
from typing import TYPE_CHECKING

import napari
import numpy as np
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton, QFileDialog
from magicgui import magicgui
from napari.utils.events.event import Event
from napari.utils.notifications import show_error
from napari_matplotlib.base import NapariMPLWidget
from psf_extractor.plotting import fire
from qtpy.QtWidgets import QWidget
from superqt import QRangeSlider

from napari_psf_extractor.extractor import get_features_plot_data
from napari_psf_extractor.utils import crop_to_bbox, normalize

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
        self.stack = None
        self.mip = None
        self.features_init = None
        self.features_layer = None

        # Widgets
        self.range_slider, self.range_label = create_range_slider_widget(min_value=0, max_value=100)
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
        self.save_button.clicked.connect(self.save_pdf)

        self.viewer.layers.events.inserted.connect(param_setter.reset_choices)
        self.viewer.layers.events.removed.connect(param_setter.reset_choices)

        # Create a QTimer to handle delayed updates
        self.features_timer = QTimer()
        self.features_timer.setSingleShot(True)
        self.features_timer.timeout.connect(self.update_features_layer)

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

            self.update_features_layer()

            # Move to next state
            self.state = 1

    def update_range_label(self, mass_range):
        """
        Update the range label. This function is called when the range slider is moved.
        """
        self.range_label.setText(f"Mass Range: [{mass_range[0]}, {mass_range[1]}]")

        # Restart the timer
        if self.features_timer.isActive():
            self.features_timer.stop()

        # Timer used to prevent excessive and rapid updates (50 ms)
        self.features_timer.start(50)

    def update_features_layer(self):
        """
        Update the features layer.
        """
        if not hasattr(self, "mip"):
            show_error("Error: Please select an image stack.")
            pass

        if self.mip is not None and isinstance(self.mip, np.ndarray):
            data = get_features_plot_data(
                self.plot_widget,
                self.mip,
                self.dx, self.dy,
                self.range_slider.value()
            )

            if not self.viewer_has_layer("Features"):
                cmap = napari.utils.Colormap(fire.colors, display_name=fire.name)
                self.features_layer = self.viewer.add_image(data=data, colormap=cmap, name='Features')

            self.features_layer.data = data

    def viewer_has_layer(self, layer_name):
        """
        Check if a layer with the given name is already present in the viewer.
        """
        return any(layer.name == layer_name for layer in self.viewer.layers)
