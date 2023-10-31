import numpy as np

from psf_extractor.plotting import fire


def plot_mass_range(ax, mip, mass, features):
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
