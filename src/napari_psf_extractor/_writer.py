from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Sequence, Tuple, Union

if TYPE_CHECKING:
    DataType = Union[Any, Sequence[Any]]
    FullLayerData = Tuple[DataType, dict, str]


def write_single_image(path: str, data: Any, meta: dict) -> List[str]:
    """
    Writes a single image layer.

    Parameters
    ----------
    path : str
        The path where the image layer will be written.

    data : Any
        The image data to be written. This could be in various formats,
        such as bytes, numpy arrays, or other suitable types.

    meta : dict
        Additional metadata related to the image. This can include information
        such as image dimensions, color space, and other relevant details.

    Returns
    -------
    List[str]
        A list containing the paths to any file(s) that were successfully written.
    """
    return [path]


def write_multiple(path: str, data: List[FullLayerData]) -> List[str]:
    """
    Writes multiple layers of different types to the specified path.

    Parameters
    ----------
    path : str
        The directory or file path where the layers will be written.

    data : List[FullLayerData]
        A list of `FullLayerData` objects, where each object represents a layer to be written.

    Returns
    -------
    List[str]
        A list containing the paths to any file(s) that were successfully written.
    """
    return [path]
