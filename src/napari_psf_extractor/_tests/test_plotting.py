import unittest
from unittest.mock import patch, Mock

import numpy as np
import pandas as pd

from ..plotting import plot_mass_range


class TestPlotting(unittest.TestCase):
    @patch('matplotlib.axes.Axes')
    @patch('matplotlib.pyplot.gcf')
    def test_plot_mass_range_aspect_ratio(self, mock_gcf, mock_axes):
        # Given
        mock_fig = Mock()
        mock_fig.dpi = 1
        mock_gcf.return_value = mock_fig
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
        mock_fig.set_size_inches.assert_called_once_with(
            mip.shape[1] / mock_fig.dpi,
            mip.shape[0] / mock_fig.dpi
        )
