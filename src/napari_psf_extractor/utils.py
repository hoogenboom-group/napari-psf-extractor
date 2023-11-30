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


def crop_to_bbox(input_array):
    """
    Crop a 2D array to the bounding box of non-transparent pixels.

    Parameters
    ----------
    input_array : np.ndarray
        2D array of shape (M, N, 4) where the last dimension is RGBA.

    Returns
    -------
    cropped_array : np.ndarray
        2D array of shape (M', N', 4) where the last dimension is RGBA.
        M' and N' are the dimensions of the bounding box of non-transparent
        pixels.
    """

    # Ensure the input_array is C-contiguous
    input_array = np.ascontiguousarray(input_array)

    # Find the bounding box of the non-transparent pixels
    non_transparent_rows = np.any(input_array[:, :, 3] > 0, axis=1)
    non_transparent_columns = np.any(input_array[:, :, 3] > 0, axis=0)

    # If the input array is completely transparent, return it
    if non_transparent_rows.sum() == 0:
        return input_array

    min_row, max_row = np.where(non_transparent_rows)[0][[0, -1]]
    min_col, max_col = np.where(non_transparent_columns)[0][[0, -1]]

    # Crop the input array to the bounding box of non-transparent pixels
    cropped_array = input_array[min_row:max_row + 1, min_col:max_col + 1]

    # Make a C-contiguous copy of the cropped array
    cropped_array = np.copy(cropped_array)

    return cropped_array


def remove_plot_background(image):
    """
    Remove the background of a matplotlib plot.

    Namely, remove the white background and crop the image to the bounding box
    """

    # Replace coloured background with transparent background
    replacement_color = [0, 0, 0, 0]

    mask = np.all(image == [255, 255, 255, 255], axis=-1)
    image[mask] = replacement_color

    # Crop to bbox to remove white space
    data = crop_to_bbox(image)

    mask = np.all(data == [0, 0, 0, 255], axis=-1)
    data[mask] = replacement_color

    return data
