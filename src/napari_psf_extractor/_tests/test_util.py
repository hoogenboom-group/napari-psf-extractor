import unittest

import numpy as np
from ..utils import normalize, crop_to_bbox


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

    def test_crop_to_bbox_simple(self):
        # Given
        input_array = np.zeros((5, 5, 4), dtype=np.uint8)

        # L shaped image
        input_array[1:3, 1:3, :] = 255
        input_array[1, 2, :] = 0

        # When
        cropped_array = crop_to_bbox(input_array)

        # Then
        expected = input_array[1:3, 1:3]
        self.assertTrue(np.array_equal(expected, cropped_array))

    def test_crop_to_bbox_zeros(self):
        # Given
        input_array = np.zeros((10, 10, 4), dtype=np.uint8)

        # When
        cropped_array = crop_to_bbox(input_array)

        # Then
        self.assertTrue(np.array_equal(input_array, cropped_array))