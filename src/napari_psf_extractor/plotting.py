import numpy as np
from matplotlib import pyplot as plt
from psf_extractor import gaussian_1D, guess_gaussian_1D_params, fit_gaussian_1D

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

    fig = plt.gcf()
    fig.set_size_inches(mip.shape[1] / fig.dpi, mip.shape[0] / fig.dpi)

    ax.imshow(background, cmap=fire)
    ax.plot(df['x'], df['y'], ls='', color='#00ff00',
            marker='o', ms=7, mfc='none', mew=1)

    return len(df)


def plot_psf(psf, psx, psy, psz):
    """
    PSF plotting function.

    Parameters
    ----------
    psf : numpy.ndarray
        The PSF to plot.
    psx : float
        The pixel size in x-direction [nm/px].
    psy : float
        The pixel size in y-direction [nm/px].
    psz : float
        The pixel size in z-direction [nm/px].

    Authors
    -------
    - Ryan Lane (lanery)
    - Daan Boltje (dbboltje)
    - Ernest van der Wee (EvdWee)

    Notes
    -----
    This is an older version of the function that was used in the
    napari-psf-extractor package. This one is more simple and does not
    allow for interactive plotting.
    """

    # clear previous plots
    plt.close('all')

    # Create figure and axes
    fig = plt.figure()
    gs = fig.add_gridspec(9, 9)
    ax_xy = fig.add_subplot(gs[:3,:3])
    ax_yz = fig.add_subplot(gs[:3,3:])
    ax_xz = fig.add_subplot(gs[3:,:3])
    ax_z = fig.add_subplot(gs[3:5,3:])
    ax_y = fig.add_subplot(gs[5:7,3:])
    ax_x = fig.add_subplot(gs[7:9,3:])

    # PSF dimensions
    Nz, Ny, Nx = psf.shape
    # PSF volume [μm]
    wz, wy, wx = 1e-3*psz*Nz, 1e-3*psy*Ny, 1e-3*psx*Nx
    # PSF center coords
    z0, y0, x0 = Nz//2, Ny//2, Nx//2

    # --- 2D Plots ---
    # Determine cropping margin
    crop_yz = int((wz - 2*wy) / (2*psz*1e-3)) if wz > 2*wy else None
    crop_xz = int((wz - 2*wx) / (2*psz*1e-3)) if wz > 2*wx else None
    # Crop 2D PSFs to 2:1 aspect ratio
    psf_xy_at_z0 = psf[z0, :, :]
    psf_xz_at_y0 = psf[crop_yz:-crop_yz, y0, :] if wz > 2*wy else psf[:, y0, :]
    psf_yz_at_x0 = psf[crop_xz:-crop_xz, :, x0] if wz > 2*wx else psf[:, :, x0]
    # Update extent (after cropping)
    wz_cropped = psf_xz_at_y0.shape[0] * 1e-3*psz
    # Plot 2D PSFs
    ax_xy.imshow(psf_xy_at_z0, cmap=fire, interpolation='none',
                 extent=[-wx/2, wx/2, -wy/2, wy/2])
    ax_yz.imshow(psf_yz_at_x0.T, cmap=fire, interpolation='none',
                 extent=[-wz_cropped/2, wz_cropped/2, -wy/2, wy/2])
    ax_xz.imshow(psf_xz_at_y0, cmap=fire, interpolation='none',
                 extent=[-wx/2, wx/2, -wz_cropped/2, wz_cropped/2])

    # --- 1D Plots ---
    # 1D PSFs (slices)
    prof_z = psf[:, y0, x0]
    prof_y = psf[z0, :, x0]
    prof_x = psf[z0, y0, :]
    # 1D Axes
    z = np.linspace(-wz/2, wz/2, prof_z.size)
    y = np.linspace(-wy/2, wy/2, prof_y.size)
    x = np.linspace(-wx/2, wx/2, prof_x.size)
    # Do 1D PSF fits
    popt_z = fit_gaussian_1D(prof_z, z, p0=guess_gaussian_1D_params(prof_z, z))
    popt_y = fit_gaussian_1D(prof_y, y, p0=guess_gaussian_1D_params(prof_y, y))
    popt_x = fit_gaussian_1D(prof_x, x, p0=guess_gaussian_1D_params(prof_x, x))
    # Plot 1D PSFs
    plot_kwargs = {'ms': 5, 'marker': 'o', 'ls': '', 'alpha': 0.75}
    ax_z.plot(z, prof_z, c='C1', label='Z', **plot_kwargs)
    ax_y.plot(y, prof_y, c='C0', label='Y', **plot_kwargs)
    ax_x.plot(x, prof_x, c='C2', label='X', **plot_kwargs)
    # Plot 1D PSF fits
    ax_z.plot(z, gaussian_1D(z, *popt_z), 'k-')
    ax_y.plot(y, gaussian_1D(y, *popt_y), 'k-')
    ax_x.plot(x, gaussian_1D(x, *popt_x), 'k-')

    # --- FWHM arrows ---
    # Z
    x0 = popt_z[0]
    y0 = popt_z[2]/2 + popt_z[3]
    fwhm = np.abs(2.355 * popt_z[1])
    ax_z.annotate('', xy=(x0-fwhm/2-0.6, y0), xytext=(x0-fwhm/2-0.1, y0), arrowprops={'arrowstyle': '<|-'})
    ax_z.annotate('', xy=(x0+fwhm/2+0.6, y0), xytext=(x0+fwhm/2+0.1, y0), arrowprops={'arrowstyle': '<|-'})
    ax_z.text(x0,popt_z[3], f'{1e3*fwhm:.0f}nm', ha='center')
    # Y
    x0 = popt_y[0]
    y0 = popt_y[2]/2 + popt_y[3]
    fwhm = np.abs(2.355 * popt_y[1])
    ax_y.annotate('', xy=(x0-fwhm/2-0.6, y0), xytext=(x0-fwhm/2-0.1, y0), arrowprops={'arrowstyle': '<|-'})
    ax_y.annotate('', xy=(x0+fwhm/2+0.6, y0), xytext=(x0+fwhm/2+0.1, y0), arrowprops={'arrowstyle': '<|-'})
    ax_y.text(x0, popt_z[3], f'{1e3*fwhm:.0f}nm', ha='center')
    # X
    x0 = popt_x[0]
    y0 = popt_x[2]/2 + popt_x[3]
    fwhm = np.abs(2.355 * popt_x[1])
    ax_x.annotate('', xy=(x0-fwhm/2-0.6, y0), xytext=(x0-fwhm/2-0.1, y0), arrowprops={'arrowstyle': '<|-'})
    ax_x.annotate('', xy=(x0+fwhm/2+0.6, y0), xytext=(x0+fwhm/2+0.1, y0), arrowprops={'arrowstyle': '<|-'})
    ax_x.text(x0, popt_z[3], f'{1e3*fwhm:.0f}nm', ha='center')

    # --- Aesthetics ---
    # XY projection
    ax_xy.text(0.02, 0.02, 'XY', color='white', fontsize=14, transform=ax_xy.transAxes)
    ax_xy.set_xlabel('X [μm]')
    ax_xy.set_ylabel('Y [μm]')
    ax_xy.xaxis.set_ticks_position('top')
    ax_xy.xaxis.set_label_position('top')
    # YZ projection
    ax_yz.text(0.02, 0.02, 'YZ', color='white', fontsize=14, transform=ax_yz.transAxes)
    ax_yz.set_xlabel('Z [μm]')
    ax_yz.set_ylabel('Y [μm]')
    ax_yz.xaxis.set_ticks_position('top')
    ax_yz.xaxis.set_label_position('top')
    ax_yz.yaxis.set_ticks_position('right')
    ax_yz.yaxis.set_label_position('right')
    # XZ projection
    ax_xz.text(0.02, 0.02, 'XZ', color='white', fontsize=14, transform=ax_xz.transAxes)
    ax_xz.set_xlabel('X [μm]')
    ax_xz.set_ylabel('Z [μm]')
    # 1D Axes
    ax_x.set_xlabel('Distance [μm]')
    [ax.set_xlim(-wy*1.1, wy*1.1) for ax in [ax_z, ax_y, ax_x]]

    # Miscellaneous
    [ax.legend(loc='upper right') for ax in [ax_z, ax_y, ax_x]]
    [ax.grid(ls=':') for ax in [ax_z, ax_y, ax_x]]
    plt.subplots_adjust(hspace=0.5, wspace=0.5)
    plt.show()
