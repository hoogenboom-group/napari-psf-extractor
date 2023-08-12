from __future__ import annotations

import numpy


def make_sample_data():
    """
    Generates an image

    Check the documentation for more information about add_image_kwargs
    https://napari.org/stable/api/napari.Viewer.html#napari.Viewer.add_image

    Returns
    -------
    List[ (data, add_image_kwargs) ]
    """
    return [(numpy.random.rand(512, 512), {})]
