import numpy as np


def normalize(input_array):
    """
    Normalize an array to the range [0, 1].
    """
    input_array = input_array.astype(float)

    imin, imax = np.min(input_array), np.max(input_array)

    if imin == imax:
        return np.ones(input_array.shape, dtype=input_array.dtype)

    # Normalize the image
    input_array -= imin
    input_array /= (imax - imin)

    return input_array

