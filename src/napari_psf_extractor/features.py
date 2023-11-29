import threading

import napari
import numpy as np
from napari._qt.qthreading import thread_worker
from napari.utils.notifications import show_error
from psf_extractor.plotting import fire

from napari_psf_extractor.extractor import get_features_plot_data


class Features:
    def __init__(self, widget):
        self.widget = widget

        self.lock = threading.Lock()

        self.data = None
        self.features_init = None
        self.features_layer = None

    @thread_worker
    def update_factory(self):
        """
        Create a worker to update the features layer.
        """
        if not hasattr(self.widget, "mip"):
            show_error("Error: Please select an image stack.")
            pass

        if self.widget.mip is not None and isinstance(self.widget.mip, np.ndarray):
            self.data, self.features_init = get_features_plot_data(
                self.widget.plot_fig,
                self.widget.mip,
                self.widget.dx, self.widget.dy,
                self.widget.mass_slider.value()
            )

    def update(self):
        """
        Update the features layer asynchronously.
        """
        if self.lock.acquire(blocking=False):
            # Mass range at the time of the update call
            curr_range = self.widget.mass_slider.value()

            self.widget.status.start_loading_animation("Finding features... ")

            worker = self.update_factory()
            worker.returned.connect(lambda: self.callback(curr_range))
            worker.start()

    def callback(self, curr_range):
        """
        Callback for the update worker.

        If the mass range has changed since the worker was created,
        then the worker is restarted.

        Parameters
        ----------
        curr_range : tuple
            The mass range at the time of the update call.
        """

        # Create features layer if it doesn't exist
        if not self.layer_exists("Features"):
            cmap = napari.utils.Colormap(fire.colors, display_name=fire.name)
            self.features_layer = self.widget.viewer.add_image(data=self.data, colormap=cmap, name='Features')

        # Update features layer
        self.features_layer.data = self.data
        self.widget.status.stop_animation()
        self.lock.release()

        # Restart if mass range changed
        if curr_range != self.widget.mass_slider.value():
            self.update()

    def get_features(self):
        return self.features_init

    def layer_exists(self, layer_name):
        """
        Check if a layer with the given name is already present in the viewer.
        """
        return any(layer.name == layer_name for layer in self.widget.viewer.layers)
