import cv2
import numpy as np
import psf_extractor as psfe
import trackpy

from napari_psf_extractor.utils import crop_to_bbox
from napari_psf_extractor.plotting import plot_mass_range


def get_features_plot_data(plot_widget, mip, dx, dy, mass):
    """
    Get plot data for the features layer.

    Parameters
    ----------
    plot_widget : napari_psf_extractor._widget.PlotWidget
        The plot widget.
    mip : np.ndarray
        The maximum intensity projection of the stack.
    dx : int
        The width of the PSF.
    dy : int
        The height of the PSF.
    mass : tuple
        The mass range to plot.

    Returns
    -------
    np.ndarray
        The plot data in the form of green circles on top of
        a transparent background.
    """
    # Clear previous plot
    plot_widget.canvas.figure.clear()
    ax = plot_widget.canvas.figure.add_subplot(111)

    # Plot features
    features_init = trackpy.locate(mip, diameter=[dy, dx]).reset_index(drop=True)

    plot_mass_range(mip=mip, ax=ax, mass=mass, features=features_init)
    plot_widget.canvas.draw()

    # Fetch plot matplotlib data from buffer
    data = np.array(plot_widget.canvas.figure.canvas.renderer.buffer_rgba())

    # Crop to bbox to remove white space
    data = crop_to_bbox(data)
    data = cv2.resize(data, dsize=mip.shape, interpolation=cv2.INTER_CUBIC)

    # Replace white background with transparent background
    replacement_color = [255, 255, 255, 0]
    mask = np.all(data == [0, 0, 0, 255], axis=-1)
    data[mask] = replacement_color

    return data, features_init


def extract_psf(min_mass, max_mass, stack, features, wx, wy, wz):
    """
    Extract a PSF from a given stack and feature set.
    """
    # Update feature set
    features_min_mass = features.loc[(features['raw_mass'] > min_mass)]
    features_mass = features.loc[(features['raw_mass'] > min_mass)
                                 & (features['raw_mass'] < max_mass)]

    overlapping = psfe.detect_overlapping_features(features_min_mass, wx, wy)

    # Detect edge features
    dz, dy, dx = stack.shape
    edges = psfe.detect_edge_features(features_mass, dx, dy, wx, wy)

    # Combine
    overlapping = np.concatenate([overlapping, edges])

    # Update feature set
    features_overlap = features_mass.loc[~features_mass.index.isin(overlapping)]

    # Extract PSFs
    psfs, features_extracted = psfe.extract_psfs(
        stack,
        features=features_overlap,
        shape=(wz, wy, wx)
    )

    # Filter locations
    locations = psfe.localize_psfs(psfs, integrate=False)

    loc_filtered, features_filtered, psfs_filtered = psfe.filt_locations(
        locations,
        features_extracted,
        psfs
    )

    # Align PSFs
    usf = 5
    psf_sum = psfe.align_psfs(psfs_filtered, loc_filtered, upsample_factor=usf)

    return psf_sum
