import unittest

import numpy as np
from ..utils import normalize


class TestUtil(unittest.TestCase):
    def test_normalize_simple(self):
        # Given
        input_array = np.array([1, 6, 11], dtype=np.uint8)

        # When
        normalized_array = normalize(input_array)

        # Then
        expected = np.array([0, 0.5, 1])
        self.assertTrue(np.array_equal(expected, normalized_array))

    def test_normalize_zeros(self):
        # Given
        input_array = np.zeros((10, 10, 4), dtype=np.uint8)

        # When
        normalized_array = normalize(input_array)

        # Then
        expected = np.ones((10, 10, 4), dtype=np.uint8)
        self.assertTrue(np.array_equal(expected, normalized_array))
