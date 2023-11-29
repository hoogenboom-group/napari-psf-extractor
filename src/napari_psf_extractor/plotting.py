import numpy as np

from psf_extractor.plotting import fire


def plot_mass_range(ax, mip, mass, features):
    """
    Plot the features in the mass range [mass[0], mass[1]].

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to plot on.
    mip : numpy.ndarray
        The maximum intensity projection of the image stack.
    mass : tuple
        The mass range to plot.
    features : pandas.DataFrame
        The features to plot.

    Returns
    -------
    int
        The number of features found.
    """

    # Enhance contrast in MIP (by taking the log)
    s = 1 / mip[mip != 0].min()  # scaling factor (such that log(min) = 0
    mip_log = np.log(s * mip,
                     out=np.zeros_like(mip),
                     where=mip != 0)  # avoid /b0 error

    df = features[(features['raw_mass'] > mass[0]) & (features['raw_mass'] < mass[1])]

    # Set up figure
    ax.axis('off')
    ax.set_title("")

    # Set the aspect ratio for the Axes to match the image
    aspect_ratio = mip_log.shape[1] / mip_log.shape[0]
    ax.set_aspect(aspect_ratio)

    background = np.ones(mip_log.shape)

    ax.imshow(background, cmap=fire)
    ax.plot(df['x'], df['y'], ls='', color='#00ff00',
            marker='o', ms=7, mfc='none', mew=1)

    return len(df)
