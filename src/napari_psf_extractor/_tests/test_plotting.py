import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from ..plotting import plot_mass_range


class TestPlotting(unittest.TestCase):
    @patch('matplotlib.axes.Axes')
    def test_plot_mass_range_aspect_ratio(self, mock_axes):
        # Given
        ax = mock_axes
        mip = np.ones((10, 10), dtype=np.float64)  # Ensure dtype is float64
        mass = (1, 4)
        features_data = {'raw_mass': [2, 3], 'x': [1, 2], 'y': [3, 4]}
        features = pd.DataFrame(features_data, dtype=np.float64)  # Ensure dtype is float64

        # When
        plot_mass_range(ax, mip, mass, features)

        # Then
        expected = mip.shape[1] / mip.shape[0]
        ax.set_aspect.assert_called_once_with(expected)
