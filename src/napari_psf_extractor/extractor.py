import cv2
import numpy as np
import psf_extractor as psfe
import trackpy

from napari_psf_extractor.plotting import plot_mass_range
from napari_psf_extractor.utils import remove_plot_background


def get_features_plot_data(plot_fig, mip, dx, dy, mass):
    """
    Get plot data for the features layer.

    Parameters
    ----------
    plot_fig : FigureCanvas
        The plot figure.
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
    plot_fig.canvas.figure.clear()
    ax = plot_fig.canvas.figure.add_subplot(111)

    # Plot features
    features_init = trackpy.locate(mip, diameter=[dy, dx]).reset_index(drop=True)

    feature_count = plot_mass_range(mip=mip, ax=ax, mass=mass, features=features_init)
    plot_fig.canvas.draw()

    # Fetch plot matplotlib data from buffer
    data = np.array(plot_fig.canvas.figure.canvas.renderer.buffer_rgba())

    data = remove_plot_background(data)

    data = cv2.resize(data, dsize=(mip.shape[1], mip.shape[0]), interpolation=cv2.INTER_NEAREST)

    return data, features_init, feature_count


def extract_psf(min_mass, max_mass, stack, features, wx, wy, wz, pcc_min, usf):
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

    # Filter PCC if enabled
    if pcc_min != None:
        features_pearson = filter_pcc(pcc_min, features_extracted, psfs)
        psfs, features_extracted = psfe.extract_psfs(stack, features=features_pearson, shape=(wz, wy, wx))

    # Filter locations
    locations = psfe.localize_psfs(psfs, integrate=False)

    loc_filtered, features_filtered, psfs_filtered = psfe.filt_locations(
        locations,
        features_extracted,
        psfs
    )

    # Align PSFs
    psf_sum = psfe.align_psfs(psfs_filtered, loc_filtered, upsample_factor=usf)

    return psf_sum, features_filtered


def filter_pcc(pcc_min, features, psfs):
    # Detect outlier PCCs
    outliers_, pccs = psfe.detect_outlier_psfs(psfs, pcc_min=pcc_min, return_pccs=True)

    df = features.reset_index()
    outliers = df[df.index.isin(outliers_)]['index'].values

    features_pearson = features.loc[~features.index.isin(outliers)]

    return features_pearson
